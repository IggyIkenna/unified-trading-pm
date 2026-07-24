---
title: Phase 0 pre-audit manifest — strategy_repo_consolidation_2026_05_19
created: 2026-05-19
author: slot-1 sub-agent (phase-0 pre-audit, READ-ONLY)
source:
  - plans/active/strategy_repo_consolidation_2026_05_19.md
  - risk-and-exposure-service/
  - position-balance-monitor-service/
  - pnl-attribution-service/
  - strategy-service/
locked_by: live-defi-rollout
---

> **🟡 COVERED BY** [../strategy_repo_consolidation_2026_05_19.md](../strategy_repo_consolidation_2026_05_19.md) — Phase
> 0 pre-audit diagnostic artefact for the named consolidation plan (slot-1 triage 2026-05-20). Important: corrects the
> earlier "ZERO cross-repo imports" fact-report — that correction must land in the parent plan body before Phase 4
> import-rewrite. Stays in issues/ until parent closes.

## Scope

Pre-audit manifest for the `strategy_repo_consolidation_2026_05_19` plan (Phase 0). Subtree-merges
`risk-and-exposure-service` → `strategy_service/risk/`, `position-balance-monitor-service` →
`strategy_service/position/`, `pnl-attribution-service` → `strategy_service/pnl/`. Drives every later phase.

**Method**: `rg --no-ignore-vcs` across the full workspace (`.tabs/1/`) with
`.venv* / build / dist / node_modules / .git / __pycache__` excluded. All counts are evidence-grounded and reproducible.

**Headline correction to fact-report 2026-05-19**: the fact-report claimed **ZERO** cross-repo Python imports. **This is
wrong.** Section (b) below documents **25 external import statements across 7 files** in 5 sibling repos. Phase 4
import-rewrite + Phase 8 launcher migration MUST include these.

---

## (a) Per-source-repo module / class / function inventory + post-merge sub-package landing

Subtree merge maps `<repo>/<package>/<file>.py` → `strategy-service/strategy_service/<sub>/<file>.py`. Tests map
`<repo>/tests/` → `strategy-service/tests/<sub>/`. Scripts map `<repo>/scripts/` → `strategy-service/scripts/<sub>/`.

### `risk-and-exposure-service` → `strategy_service/risk/`

Package root: `risk_and_exposure_service/`. **64 Python files** total.

| Path (source)                                                        | Post-merge landing                                                                            |
| -------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `risk_and_exposure_service/__init__.py`                              | `strategy_service/risk/__init__.py`                                                           |
| `risk_and_exposure_service/__main__.py`                              | `strategy_service/risk/__main__.py` (DROP — Phase 4 unifies entry)                            |
| `risk_and_exposure_service/auth_s2s.py`                              | `strategy_service/risk/auth_s2s.py` (71 LOC — real impl; see § (f))                           |
| `risk_and_exposure_service/circuit_breaker_registry.py`              | `strategy_service/risk/circuit_breaker_registry.py`                                           |
| `risk_and_exposure_service/config.py`                                | `strategy_service/risk/config.py` (will be folded into root config)                           |
| `risk_and_exposure_service/config_reloaders.py`                      | `strategy_service/risk/config_reloaders.py` (152 LOC — see § (f))                             |
| `risk_and_exposure_service/isolation_policy.py`                      | `strategy_service/risk/isolation_policy.py` (93 LOC — see § (f))                              |
| `risk_and_exposure_service/kill_switch_bus_subscriber.py`            | `strategy_service/risk/kill_switch_bus_subscriber.py` (§ (f))                                 |
| `risk_and_exposure_service/metrics.py`                               | `strategy_service/risk/metrics.py`                                                            |
| `risk_and_exposure_service/models.py`                                | `strategy_service/risk/models.py` (1 class: `RiskLimits`, marked CORRECT-LOCAL)               |
| `risk_and_exposure_service/pre_crash_checkpoint.py`                  | `strategy_service/risk/pre_crash_checkpoint.py`                                               |
| `risk_and_exposure_service/recovery_loop.py`                         | `strategy_service/risk/recovery_loop.py`                                                      |
| `risk_and_exposure_service/scenario_outcome_bridge.py`               | `strategy_service/risk/scenario_outcome_bridge.py`                                            |
| `risk_and_exposure_service/adapters/alert_adapter.py`                | `strategy_service/risk/adapters/alert_adapter.py`                                             |
| `risk_and_exposure_service/adapters/position_adapter.py`             | `strategy_service/risk/adapters/position_adapter.py`                                          |
| `risk_and_exposure_service/api/main.py`                              | MERGE into `strategy_service/api/main.py` aggregator (Phase 4 (c))                            |
| `risk_and_exposure_service/cli/main.py`                              | DROP — Phase 4 unifies CLI under `strategy_service/cli/main.py` `--operation risk-monitor`    |
| `risk_and_exposure_service/cli/parser.py`                            | `strategy_service/risk/cli/parser.py`                                                         |
| `risk_and_exposure_service/cli/handlers/compute_handler.py`          | `strategy_service/risk/cli/handlers/compute_handler.py`                                       |
| `risk_and_exposure_service/core/aggregated_position_subscriber.py`   | `strategy_service/risk/core/aggregated_position_subscriber.py`                                |
| `risk_and_exposure_service/core/alert_manager.py`                    | `strategy_service/risk/core/alert_manager.py`                                                 |
| `risk_and_exposure_service/core/commodity_checks.py`                 | `strategy_service/risk/core/commodity_checks.py`                                              |
| `risk_and_exposure_service/core/correlation_matrix.py`               | `strategy_service/risk/core/correlation_matrix.py`                                            |
| `risk_and_exposure_service/core/defi_reconciliation.py`              | `strategy_service/risk/core/defi_reconciliation.py`                                           |
| `risk_and_exposure_service/core/exposure_aggregator.py`              | `strategy_service/risk/core/exposure_aggregator.py`                                           |
| `risk_and_exposure_service/core/greeks_risk.py`                      | `strategy_service/risk/core/greeks_risk.py`                                                   |
| `risk_and_exposure_service/core/leverage_breach_detector.py`         | `strategy_service/risk/core/leverage_breach_detector.py` (external consumer — see (b))        |
| `risk_and_exposure_service/core/monte_carlo_var.py`                  | `strategy_service/risk/core/monte_carlo_var.py`                                               |
| `risk_and_exposure_service/core/position_monitor_client.py`          | `strategy_service/risk/core/position_monitor_client.py` (becomes in-process call after merge) |
| `risk_and_exposure_service/core/pre_trade_check_engine.py`           | `strategy_service/risk/core/pre_trade_check_engine.py`                                        |
| `risk_and_exposure_service/core/regime_detector.py`                  | `strategy_service/risk/core/regime_detector.py`                                               |
| `risk_and_exposure_service/core/returns_store.py`                    | `strategy_service/risk/core/returns_store.py`                                                 |
| `risk_and_exposure_service/core/risk_calculator.py`                  | `strategy_service/risk/core/risk_calculator.py`                                               |
| `risk_and_exposure_service/core/risk_dimensions/duration.py`         | `strategy_service/risk/core/risk_dimensions/duration.py`                                      |
| `risk_and_exposure_service/core/risk_dimensions/second_order_vol.py` | `strategy_service/risk/core/risk_dimensions/second_order_vol.py`                              |
| `risk_and_exposure_service/core/risk_dimensions/spread.py`           | `strategy_service/risk/core/risk_dimensions/spread.py`                                        |
| `risk_and_exposure_service/core/risk_dimensions/venue_protocol.py`   | `strategy_service/risk/core/risk_dimensions/venue_protocol.py`                                |
| `risk_and_exposure_service/core/risk_limits_client_factory.py`       | `strategy_service/risk/core/risk_limits_client_factory.py`                                    |
| `risk_and_exposure_service/core/risk_limits_protocol.py`             | `strategy_service/risk/core/risk_limits_protocol.py`                                          |
| `risk_and_exposure_service/core/risk_monitor.py`                     | `strategy_service/risk/core/risk_monitor.py`                                                  |
| `risk_and_exposure_service/core/risk_snapshot_sink.py`               | `strategy_service/risk/core/risk_snapshot_sink.py`                                            |
| `risk_and_exposure_service/core/sse_risk_alerts.py`                  | `strategy_service/risk/core/sse_risk_alerts.py`                                               |
| `risk_and_exposure_service/core/var_attribution.py`                  | `strategy_service/risk/core/var_attribution.py`                                               |
| `risk_and_exposure_service/core/var_calculator.py`                   | `strategy_service/risk/core/var_calculator.py`                                                |
| `risk_and_exposure_service/engine/mock_data_provider.py`             | `strategy_service/risk/engine/mock_data_provider.py`                                          |
| `risk_and_exposure_service/engine/orchestrator.py`                   | `strategy_service/risk/engine/orchestrator.py`                                                |
| `risk_and_exposure_service/engine/risk_metrics.py`                   | `strategy_service/risk/engine/risk_metrics.py` (external consumer — (b))                      |
| `risk_and_exposure_service/engine/sports_risk.py`                    | `strategy_service/risk/engine/sports_risk.py` (external consumer — (b))                       |
| `risk_and_exposure_service/v2/correlation_cap.py`                    | `strategy_service/risk/v2/correlation_cap.py`                                                 |
| `risk_and_exposure_service/v2/greek_model.py`                        | `strategy_service/risk/v2/greek_model.py`                                                     |
| `risk_and_exposure_service/v2/kill_switch_rules.py`                  | `strategy_service/risk/v2/kill_switch_rules.py`                                               |
| `risk_and_exposure_service/v2/margin_sim.py`                         | `strategy_service/risk/v2/margin_sim.py`                                                      |
| `risk_and_exposure_service/v2/orchestrator.py`                       | `strategy_service/risk/v2/orchestrator.py` (external consumer — (b))                          |
| `risk_and_exposure_service/v2/preflight.py`                          | `strategy_service/risk/v2/preflight.py` (external consumer — (b))                             |
| `risk_and_exposure_service/pre_trade/__init__.py`                    | `strategy_service/risk/pre_trade/__init__.py`                                                 |

### `position-balance-monitor-service` → `strategy_service/position/`

Package root: `position_balance_monitor_service/`. **86 Python files** total.

| Path (source) — by sub-tree                                                                                                                                                | Post-merge landing                                                                   |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `position_balance_monitor_service/{__init__,__main__,auth_s2s,config,config_reloaders,isolation_policy,kill_switch_bus_subscriber,metrics,models}.py`                      | `strategy_service/position/<file>.py` (top-level shims; § (f))                       |
| `position_balance_monitor_service/api/main.py`                                                                                                                             | MERGE into `strategy_service/api/main.py` (Phase 4 (c))                              |
| `position_balance_monitor_service/api/margin_health.py`                                                                                                                    | `strategy_service/position/api/margin_health.py`                                     |
| `position_balance_monitor_service/api/reconciliation_routes.py`                                                                                                            | `strategy_service/position/api/reconciliation_routes.py`                             |
| `position_balance_monitor_service/api/routes/{aggregated,nav_snapshot,pnl_series,positions_health,positions_stream,reconciliation,risk,trades,treasury}.py`                | `strategy_service/position/api/routes/<file>.py`                                     |
| `position_balance_monitor_service/cli/{main,parser,service_entry}.py`                                                                                                      | DROP main/service_entry (Phase 4 unifies); `strategy_service/position/cli/parser.py` |
| `position_balance_monitor_service/cli/handlers/{monitor_handler,nav_snapshot_handler}.py`                                                                                  | `strategy_service/position/cli/handlers/<file>.py`                                   |
| `position_balance_monitor_service/core/account_query_client.py`                                                                                                            | `strategy_service/position/core/account_query_client.py`                             |
| `position_balance_monitor_service/core/balance_reconciliation_engine.py`                                                                                                   | `strategy_service/position/core/balance_reconciliation_engine.py`                    |
| `position_balance_monitor_service/core/client_id_resolver.py`                                                                                                              | `strategy_service/position/core/client_id_resolver.py`                               |
| `position_balance_monitor_service/core/correction_dispatcher.py`                                                                                                           | `strategy_service/position/core/correction_dispatcher.py` (ext (b))                  |
| `position_balance_monitor_service/core/correlation_config.py`                                                                                                              | `strategy_service/position/core/correlation_config.py`                               |
| `position_balance_monitor_service/core/cross_venue_aggregator.py`                                                                                                          | `strategy_service/position/core/cross_venue_aggregator.py`                           |
| `position_balance_monitor_service/core/defi_health_aggregator.py`                                                                                                          | `strategy_service/position/core/defi_health_aggregator.py`                           |
| `position_balance_monitor_service/core/defi_lp_aggregator.py`                                                                                                              | `strategy_service/position/core/defi_lp_aggregator.py`                               |
| `position_balance_monitor_service/core/defi_staking_aggregator.py`                                                                                                         | `strategy_service/position/core/defi_staking_aggregator.py`                          |
| `position_balance_monitor_service/core/deviation_tracker.py`                                                                                                               | `strategy_service/position/core/deviation_tracker.py`                                |
| `position_balance_monitor_service/core/dual_failure_detector.py`                                                                                                           | `strategy_service/position/core/dual_failure_detector.py`                            |
| `position_balance_monitor_service/core/fee_reconciliation_engine.py`                                                                                                       | `strategy_service/position/core/fee_reconciliation_engine.py`                        |
| `position_balance_monitor_service/core/fill_event_consumer.py`                                                                                                             | `strategy_service/position/core/fill_event_consumer.py`                              |
| `position_balance_monitor_service/core/greeks_aggregator.py`                                                                                                               | `strategy_service/position/core/greeks_aggregator.py`                                |
| `position_balance_monitor_service/core/leg_snapshot_builder.py`                                                                                                            | `strategy_service/position/core/leg_snapshot_builder.py` (ext (b))                   |
| `position_balance_monitor_service/core/margin_event_emitter.py`                                                                                                            | `strategy_service/position/core/margin_event_emitter.py`                             |
| `position_balance_monitor_service/core/mark_price_subscriber.py`                                                                                                           | `strategy_service/position/core/mark_price_subscriber.py`                            |
| `position_balance_monitor_service/core/nav_snapshot_publisher.py`                                                                                                          | `strategy_service/position/core/nav_snapshot_publisher.py`                           |
| `position_balance_monitor_service/core/pnl_attribution_aggregator.py`                                                                                                      | `strategy_service/position/core/pnl_attribution_aggregator.py`                       |
| `position_balance_monitor_service/core/pnl_reconciliation_engine.py`                                                                                                       | `strategy_service/position/core/pnl_reconciliation_engine.py`                        |
| `position_balance_monitor_service/core/position_drift_monitor.py`                                                                                                          | `strategy_service/position/core/position_drift_monitor.py`                           |
| `position_balance_monitor_service/core/position_tracker.py`                                                                                                                | `strategy_service/position/core/position_tracker.py`                                 |
| `position_balance_monitor_service/core/reconciler_breaker_bridge.py`                                                                                                       | `strategy_service/position/core/reconciler_breaker_bridge.py`                        |
| `position_balance_monitor_service/core/reconciliation_engine.py`                                                                                                           | `strategy_service/position/core/reconciliation_engine.py`                            |
| `position_balance_monitor_service/core/risk_group_aggregator.py`                                                                                                           | `strategy_service/position/core/risk_group_aggregator.py`                            |
| `position_balance_monitor_service/core/rule_eval_context_builder.py`                                                                                                       | `strategy_service/position/core/rule_eval_context_builder.py`                        |
| `position_balance_monitor_service/core/scenario_injector.py`                                                                                                               | `strategy_service/position/core/scenario_injector.py`                                |
| `position_balance_monitor_service/core/scenario_kill_switch_subscriber.py`                                                                                                 | `strategy_service/position/core/scenario_kill_switch_subscriber.py`                  |
| `position_balance_monitor_service/core/sports_arb_engine.py`                                                                                                               | `strategy_service/position/core/sports_arb_engine.py`                                |
| `position_balance_monitor_service/core/sports_position_tracker.py`                                                                                                         | `strategy_service/position/core/sports_position_tracker.py` (ext)                    |
| `position_balance_monitor_service/core/startup_reconciler.py`                                                                                                              | `strategy_service/position/core/startup_reconciler.py`                               |
| `position_balance_monitor_service/core/transfer_reconciler.py`                                                                                                             | `strategy_service/position/core/transfer_reconciler.py`                              |
| `position_balance_monitor_service/core/treasury_monitor.py`                                                                                                                | `strategy_service/position/core/treasury_monitor.py` (ext (b))                       |
| `position_balance_monitor_service/core/venue_balance_tracker.py`                                                                                                           | `strategy_service/position/core/venue_balance_tracker.py`                            |
| `position_balance_monitor_service/core/webhook_dispatcher.py`                                                                                                              | `strategy_service/position/core/webhook_dispatcher.py`                               |
| `position_balance_monitor_service/adapters/{domain_adapter,position_store_adapter}.py`                                                                                     | `strategy_service/position/adapters/<file>.py`                                       |
| `position_balance_monitor_service/demo/seed_demo_positions.py`                                                                                                             | `strategy_service/position/demo/seed_demo_positions.py`                              |
| `position_balance_monitor_service/engine/{mock_data_provider,orchestrator}.py`                                                                                             | `strategy_service/position/engine/<file>.py`                                         |
| `position_balance_monitor_service/position_interface/{base,factory,routing,schemas}.py`                                                                                    | `strategy_service/position/position_interface/<file>.py`                             |
| `position_balance_monitor_service/position_interface/adapters/{_defi_rpc,aave,betfair,binance,bybit,ccxt,deribit,hyperliquid,ibkr,morpho,okx,polymarket,uniswap,upbit}.py` | `strategy_service/position/position_interface/adapters/<file>.py`                    |
| `position_balance_monitor_service/storage/{database,position_store}.py`                                                                                                    | `strategy_service/position/storage/<file>.py`                                        |
| `position_balance_monitor_service/v2/{attribution,invariants,projections,recon_freshness,records}.py`                                                                      | `strategy_service/position/v2/<file>.py` (ext (b))                                   |

### `pnl-attribution-service` → `strategy_service/pnl/`

Package root: `pnl_attribution_service/`. **31 Python files** total.

| Path (source)                                                                                                                         | Post-merge landing                                            |
| ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| `pnl_attribution_service/{__init__,__main__,auth_s2s,config,config_reloaders,isolation_policy,kill_switch_bus_subscriber,metrics}.py` | `strategy_service/pnl/<file>.py` (§ (f))                      |
| `pnl_attribution_service/adapters/domain_adapter.py`                                                                                  | `strategy_service/pnl/adapters/domain_adapter.py`             |
| `pnl_attribution_service/analytics/performance.py`                                                                                    | `strategy_service/pnl/analytics/performance.py`               |
| `pnl_attribution_service/api/main.py`                                                                                                 | MERGE into `strategy_service/api/main.py` (Phase 4 (c))       |
| `pnl_attribution_service/cli/{main,parser}.py`                                                                                        | DROP main; `strategy_service/pnl/cli/parser.py`               |
| `pnl_attribution_service/cli/handlers/compute_handler.py`                                                                             | `strategy_service/pnl/cli/handlers/compute_handler.py`        |
| `pnl_attribution_service/engine/archetype_aggregator.py`                                                                              | `strategy_service/pnl/engine/archetype_aggregator.py`         |
| `pnl_attribution_service/engine/breakdown.py`                                                                                         | `strategy_service/pnl/engine/breakdown.py` (ext (b))          |
| `pnl_attribution_service/engine/mock_data_provider.py`                                                                                | `strategy_service/pnl/engine/mock_data_provider.py`           |
| `pnl_attribution_service/engine/orchestrator.py`                                                                                      | `strategy_service/pnl/engine/orchestrator.py`                 |
| `pnl_attribution_service/engine/pnl_input_builder.py`                                                                                 | `strategy_service/pnl/engine/pnl_input_builder.py`            |
| `pnl_attribution_service/engine/reward_attribution.py`                                                                                | `strategy_service/pnl/engine/reward_attribution.py` (ext (b)) |
| `pnl_attribution_service/engine/reward_attribution_drain.py`                                                                          | `strategy_service/pnl/engine/reward_attribution_drain.py`     |
| `pnl_attribution_service/engine/sports_pnl.py`                                                                                        | `strategy_service/pnl/engine/sports_pnl.py` (ext (b))         |
| `pnl_attribution_service/engine/types.py`                                                                                             | `strategy_service/pnl/engine/types.py`                        |
| `pnl_attribution_service/execution_alpha/calculator.py`                                                                               | `strategy_service/pnl/execution_alpha/calculator.py`          |

### Architectural collision flag (post-merge)

`strategy-service/strategy_service/models/` is an **existing directory** containing `instruction.py`,
`output_schemas.py`, **`pnl.py`** and **`position.py`**. After subtree-merge, there will be:

- `strategy_service/models/position.py` (existing — strategy's own position model)
- `strategy_service/position/models.py` (new — PBM's `Position`, `LocalFillRecord`, `ReconciliationSnapshot`,
  `PositionResponse`, etc.)
- `strategy_service/models/pnl.py` (existing)
- `strategy_service/pnl/...` (new — no `models.py` in pnl-attribution-service; CLEAN)
- `strategy_service/risk/models.py` (new — RiskLimits)

These are **conceptually overlapping but symbol-disjoint**. Phase 4 should review and consider folding
`strategy_service/models/{position,pnl}.py` into the new sub-packages OR retaining as facade re-exports. **Mark in plan
as P1 follow-up — NOT cutover-blocking.**

---

## (b) External callsites importing `risk_and_exposure_service.*` / `position_balance_monitor_service.*` / `pnl_attribution_service.*`

**Headline**: **25 import statements across 7 files in 5 sibling repos**. Fact-report 2026-05-19 said ZERO; this is
materially wrong.

Grep command (reproducible, verified):

```bash
cd $WORKSPACE_ROOT
rg --type py -n "from risk_and_exposure_service|import risk_and_exposure_service|from position_balance_monitor_service|import position_balance_monitor_service|from pnl_attribution_service|import pnl_attribution_service" \
   -g '!.venv*' -g '!build' -g '!dist' -g '!node_modules' -g '!.git' --no-ignore-vcs \
  | grep -v -E "^(risk-and-exposure-service|position-balance-monitor-service|pnl-attribution-service)/"
```

| #   | Consumer repo              | File:line                                                         | Import statement (verbatim)                                                                                           | Post-merge replacement                                                                                         |
| --- | -------------------------- | ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| 1   | `deployment-api`           | `deployment_api/routes/treasury_routes.py:26-29`                  | `from position_balance_monitor_service.core.treasury_monitor import (compute_nav_by_client, compute_unified_nav,)`    | `from strategy_service.position.core.treasury_monitor import (compute_nav_by_client, compute_unified_nav,)`    |
| 2   | `execution-service`        | `execution_service/algo_library/leg_controller_runner.py:222-224` | `from position_balance_monitor_service.core.leg_snapshot_builder import (build_leg_snapshots,)`                       | `from strategy_service.position.core.leg_snapshot_builder import (build_leg_snapshots,)`                       |
| 3   | `e2e-testing`              | `scripts/defi/colocated_engine.py:253-257`                        | `from position_balance_monitor_service.core.treasury_monitor import (TreasuryConfig, TreasuryMonitor, WalletConfig,)` | `from strategy_service.position.core.treasury_monitor import (TreasuryConfig, TreasuryMonitor, WalletConfig,)` |
| 4   | `e2e-testing`              | `scripts/defi/colocated_engine.py:761`                            | `from pnl_attribution_service.engine.breakdown import compute_pnl_breakdown`                                          | `from strategy_service.pnl.engine.breakdown import compute_pnl_breakdown`                                      |
| 5   | `e2e-testing`              | `scripts/defi/colocated_engine.py:838-840`                        | `from risk_and_exposure_service.engine.risk_metrics import (  # noqa: I001  compute_risk_metrics,)`                   | `from strategy_service.risk.engine.risk_metrics import (compute_risk_metrics,)`                                |
| 6   | `e2e-testing`              | `tests/integration/test_architecture_v2_roundtrip.py:24-27`       | `from position_balance_monitor_service.v2.attribution import (FillAttributor, InstructionRegistration,)`              | `from strategy_service.position.v2.attribution import (FillAttributor, InstructionRegistration,)`              |
| 7   | `e2e-testing`              | `tests/integration/test_architecture_v2_roundtrip.py:28`          | `from position_balance_monitor_service.v2.projections import DualProjection`                                          | `from strategy_service.position.v2.projections import DualProjection`                                          |
| 8   | `e2e-testing`              | `tests/integration/test_architecture_v2_roundtrip.py:29`          | `from position_balance_monitor_service.v2.records import V2Fill`                                                      | `from strategy_service.position.v2.records import V2Fill`                                                      |
| 9   | `e2e-testing`              | `tests/integration/test_architecture_v2_roundtrip.py:30`          | `from risk_and_exposure_service.v2.orchestrator import FourLayerGateOrchestrator`                                     | `from strategy_service.risk.v2.orchestrator import FourLayerGateOrchestrator`                                  |
| 10  | `e2e-testing`              | `tests/integration/test_architecture_v2_roundtrip.py:31`          | `from risk_and_exposure_service.v2.preflight import PortfolioContext`                                                 | `from strategy_service.risk.v2.preflight import PortfolioContext`                                              |
| 11  | `system-integration-tests` | `tests/integration/test_recon_rebalancing.py:44`                  | `from position_balance_monitor_service.core.correction_dispatcher import CorrectionDispatcher`                        | `from strategy_service.position.core.correction_dispatcher import CorrectionDispatcher`                        |
| 12  | `system-integration-tests` | `tests/integration/test_recon_rebalancing.py:45`                  | `from position_balance_monitor_service.models import ReconciliationSnapshot`                                          | `from strategy_service.position.models import ReconciliationSnapshot`                                          |
| 13  | `system-integration-tests` | `tests/integration/test_recon_rebalancing.py:96`                  | `from position_balance_monitor_service.core.correction_dispatcher import CorrectionDispatcher`                        | `from strategy_service.position.core.correction_dispatcher import CorrectionDispatcher`                        |
| 14  | `system-integration-tests` | `tests/integration/test_recon_rebalancing.py:97`                  | `from position_balance_monitor_service.models import ReconciliationSnapshot`                                          | `from strategy_service.position.models import ReconciliationSnapshot`                                          |
| 15  | `system-integration-tests` | `tests/integration/test_recon_rebalancing.py:130`                 | `from position_balance_monitor_service.core.correction_dispatcher import CorrectionDispatcher`                        | `from strategy_service.position.core.correction_dispatcher import CorrectionDispatcher`                        |
| 16  | `system-integration-tests` | `tests/integration/test_recon_rebalancing.py:131`                 | `from position_balance_monitor_service.models import ReconciliationSnapshot`                                          | `from strategy_service.position.models import ReconciliationSnapshot`                                          |
| 17  | `system-integration-tests` | `tests/integration/test_phase6_reward_realisation_e2e.py:50-52`   | `from pnl_attribution_service.engine.reward_attribution import (attribute_reward_realisation_from_rows,)`             | `from strategy_service.pnl.engine.reward_attribution import (attribute_reward_realisation_from_rows,)`         |
| 18  | `system-integration-tests` | `tests/integration/test_leveraged_leg_controller_e2e.py:123`      | `from position_balance_monitor_service.core.leg_snapshot_builder import build_leg_snapshots`                          | `from strategy_service.position.core.leg_snapshot_builder import build_leg_snapshots`                          |
| 19  | `system-integration-tests` | `tests/integration/test_leveraged_leg_controller_e2e.py:213-215`  | `from risk_and_exposure_service.core.leverage_breach_detector import (detect_leverage_breaches,)`                     | `from strategy_service.risk.core.leverage_breach_detector import (detect_leverage_breaches,)`                  |
| 20  | `system-integration-tests` | `tests/integration/test_leveraged_leg_controller_e2e.py:249`      | `from position_balance_monitor_service.core.leg_snapshot_builder import build_leg_snapshots`                          | `from strategy_service.position.core.leg_snapshot_builder import build_leg_snapshots`                          |
| 21  | `system-integration-tests` | `tests/integration/test_leveraged_leg_controller_e2e.py:250-252`  | `from risk_and_exposure_service.core.leverage_breach_detector import (detect_leverage_breaches,)`                     | `from strategy_service.risk.core.leverage_breach_detector import (detect_leverage_breaches,)`                  |
| 22  | `system-integration-tests` | `tests/smoke/test_sports_arb_pipeline.py:135`                     | `from risk_and_exposure_service.engine.sports_risk import SportsRiskEngine`                                           | `from strategy_service.risk.engine.sports_risk import SportsRiskEngine`                                        |
| 23  | `system-integration-tests` | `tests/smoke/test_sports_arb_pipeline.py:143-145`                 | `from position_balance_monitor_service.engine.sports_position_tracker import (SportsPositionTracker,)`                | `from strategy_service.position.engine.sports_position_tracker import (SportsPositionTracker,)`                |
| 24  | `system-integration-tests` | `tests/smoke/test_sports_arb_pipeline.py:157`                     | `from pnl_attribution_service.engine.sports_pnl import SportsPnLEngine`                                               | `from strategy_service.pnl.engine.sports_pnl import SportsPnLEngine`                                           |
| 25  | `system-integration-tests` | `tests/smoke/test_sports_arb_pipeline.py:165`                     | `from pnl_attribution_service.engine.sports_pnl import SportsPnLEngine`                                               | `from strategy_service.pnl.engine.sports_pnl import SportsPnLEngine`                                           |

**Critical consumers** (NOT in tests — production code paths):

- `deployment-api/deployment_api/routes/treasury_routes.py` (item 1) — production REST endpoint. **Phase 4 MUST rewrite
  this same-turn-as-merge or deployment-api boot will break.**
- `execution-service/execution_service/algo_library/leg_controller_runner.py` (item 2) — production execution path.
  Function-local import (line 222 inside a function body), so failure is deferred until the runner is invoked — easier
  to miss in a smoke test.
- `e2e-testing/scripts/defi/colocated_engine.py` (items 3-5) — the **primary May-23 promote CLI path** (`run-paper.sh` →
  `colocated_engine.py` → `run-live.sh` per CLAUDE.md). Function-local imports inside conditional bodies; will break
  only when the relevant code-path is exercised — high cutover risk if missed.

**Verification of completeness**: also grepped for `import risk_and_exposure_service` /
`import position_balance_monitor_service` / `import pnl_attribution_service` (bare-import form, not `from ... import`).
Zero additional hits.

**Note on system-integration-tests**: many imports there are inside `try/except ImportError` blocks (banned pattern per
CLAUDE.md "no try/except ImportError"). Phase 4 should remove those guards because post-consolidation the imports are
unconditional intra-package.

---

## (c) Per-repo `scripts/` inventory + post-merge home

### `risk-and-exposure-service/scripts/`

| Path                                                | Post-merge home                                                                 |
| --------------------------------------------------- | ------------------------------------------------------------------------------- |
| `scripts/backtest_depeg_ladder.py`                  | `strategy-service/scripts/risk/backtest_depeg_ladder.py`                        |
| `scripts/seed_mock_data.py`                         | `strategy-service/scripts/risk/seed_mock_data.py`                               |
| `scripts/setup-workspace.sh`                        | DROP (duplicated across repos; use strategy-service's)                          |
| `scripts/setup.sh`                                  | DROP (duplicated)                                                               |
| `scripts/quality-gates.sh`                          | DROP (use strategy-service's own)                                               |
| `scripts/quality_gates/coverage_targets_local.yaml` | MERGE into strategy-service `scripts/quality_gates/coverage_targets_local.yaml` |

### `position-balance-monitor-service/scripts/`

| Path                                                | Post-merge home                                                 |
| --------------------------------------------------- | --------------------------------------------------------------- |
| `scripts/capture_phase_9_evidence.py`               | `strategy-service/scripts/position/capture_phase_9_evidence.py` |
| `scripts/seed_mock_data.py`                         | `strategy-service/scripts/position/seed_mock_data.py`           |
| `scripts/setup-workspace.sh`                        | DROP                                                            |
| `scripts/setup.sh`                                  | DROP                                                            |
| `scripts/quality-gates.sh`                          | DROP                                                            |
| `scripts/quality_gates/coverage_targets_local.yaml` | MERGE                                                           |

Additionally referenced by `deployment-service/scripts/vm/launch-wallet-treasury-cutover-vm.sh` (lines 89, 163,
213, 249) — Phase 8A must update those references.

### `pnl-attribution-service/scripts/`

| Path                                                | Post-merge home                                                       |
| --------------------------------------------------- | --------------------------------------------------------------------- |
| `scripts/aggregate_archetype_pnl_from_tracer.py`    | `strategy-service/scripts/pnl/aggregate_archetype_pnl_from_tracer.py` |
| `scripts/seed_mock_data.py`                         | `strategy-service/scripts/pnl/seed_mock_data.py`                      |
| `scripts/setup-workspace.sh`                        | DROP                                                                  |
| `scripts/setup.sh`                                  | DROP                                                                  |
| `scripts/quality-gates.sh`                          | DROP                                                                  |
| `scripts/quality_gates/coverage_targets_local.yaml` | MERGE                                                                 |

---

## (d) Per-repo `tests/` inventory + post-merge home

### `risk-and-exposure-service/tests/` (38 test files)

`tests/conftest.py` → `strategy-service/tests/risk/conftest.py` (fixture rename per Phase 4 (f) to `risk_<fixture>` to
avoid collision).

`tests/integration/*` (6 files) → `strategy-service/tests/risk/integration/*`. Specifically:
`test_exposure_calculation_integration.py`, `test_library_deps_integration.py`, `test_pre_trade_check_integration.py`,
`test_split_libraries.py`, `test_unified_deps_functional.py`, `test_var_pretrade.py`.

`tests/test_emission_policy_risk_state.py` → `strategy-service/tests/risk/test_emission_policy_risk_state.py`.

`tests/unit/core/*` (5 files: `test_defi_reconciliation.py`, `test_returns_store.py`, `test_risk_dimensions.py`,
`test_var_advanced.py`, `test_var_attribution_regime.py`, `test_var_calculator.py`) →
`strategy-service/tests/risk/unit/core/*`.

`tests/unit/v2/*` (3 files: `test_correlation_cap_and_greek.py`, `test_risk_rule_synthetic_fire.py`, `test_v2_risk.py`)
→ `strategy-service/tests/risk/unit/v2/*`.

`tests/unit/test_*.py` (29 files) → `strategy-service/tests/risk/unit/test_*.py`.

### `position-balance-monitor-service/tests/` (~70 test files + 12 VCR cassette YAML files)

`tests/conftest.py` → `strategy-service/tests/position/conftest.py` (fixture rename: `position_<fixture>`).

`tests/integration/*` (6 files) → `strategy-service/tests/position/integration/*`.

`tests/position_interface/` whole subtree (conftest + unit/ + integration/ + cassettes/ + mocks/) →
`strategy-service/tests/position/position_interface/` (preserve YAML cassettes verbatim).

`tests/unit/*.py` (~45 test\_\*.py + `demo/test_seed_demo_positions.py` + `v2/test_recon_and_child_venue.py`

- `v2/test_v2_pbms.py`) → `strategy-service/tests/position/unit/*`.

**PYTEST_UNIT_DIR override trigger**: PBM has a deep tree `tests/position_interface/unit/` that the default collector
won't reach. Post-merge, strategy-service's `quality-gates.sh` MUST set `PYTEST_UNIT_DIR="tests/"` BEFORE sourcing
`base-service.sh`. Phase 4 (g) covers this.

### `pnl-attribution-service/tests/` (24 test files; `__pycache__/` excluded)

`tests/conftest.py` → `strategy-service/tests/pnl/conftest.py` (fixture rename: `pnl_<fixture>`).

`tests/integration/*` (3 files: `test_library_deps_integration.py`, `test_pnl_integration.py`,
`test_unified_deps_functional.py`) → `strategy-service/tests/pnl/integration/*`.

`tests/unit/*.py` (23 files: `test_analytics.py`, `test_archetype_pnl.py`, `test_asset_group_pnl_rollup.py`,
`test_breakdown_isolation_gating.py`, `test_compute_handler_logic.py`, `test_config.py`, `test_config_reloaders.py`,
`test_defi_pnl_static.py`, `test_domain_adapter.py`, `test_engine.py`, `test_event_logging.py`,
`test_execution_alpha.py`, `test_hedge_ratio_snapshot_reader.py`, `test_isolation_policy.py`,
`test_kill_switch_bus_subscriber.py`, `test_mock_data_provider.py`, `test_parser.py`, `test_pnl_input_builder.py`,
`test_reward_attribution.py`, `test_reward_attribution_drain.py`, `test_reward_pnl_breakdown.py`,
`test_schema_robustness.py`, `test_service_startup.py`, `test_share_class_pnl.py`, `test_sports_pnl.py`) →
`strategy-service/tests/pnl/unit/*`.

### Fixture-collision audit (per Phase 4 (f))

All 3 source repos have `tests/conftest.py` + several share these test filenames (collision risk if flattened):
`test_alert_code_propagation.py` (risk + position), `test_config.py` (all three), `test_config_reloaders.py` (all
three), `test_event_logging.py` (all three), `test_isolation_policy.py` (all three),
`test_kill_switch_bus_subscriber.py` (all three), `test_mock_data_provider.py` (pnl + risk), `test_schema_robustness.py`
(all three), `test_service_startup.py` (all three), `test_adapters.py` (risk + position).

Subtree-merge into `tests/risk/`, `tests/position/`, `tests/pnl/` resolves filename collision by prefix-path.
**Fixture-name collision** (same fixture name, different impl) is the residual risk — Phase 4 (f) MUST rename fixtures
with `risk_` / `position_` / `pnl_` prefixes OR scope fixtures via per-conftest isolation. Spot check (quick pass): each
conftest is local to its subtree post-merge, so default pytest fixture-resolution will respect locality. Concrete
renames only needed if any test in `tests/strategy/` (existing) imports a fixture by name that now also exists in one of
the merged sub-trees. Phase 4 verification step:
`grep -rE "^def (risk_|position_|pnl_)?[a-z_]+\(.*\):$" tests/*/conftest.py` + diff.

---

## (e) UAC / UTL symbols redefined locally (Citadel-Grade § 7 SSOT)

Imports from upstream are already healthy: risk repo imports UAC 36×, UTL 23×; PBM 63× UAC, 46× UTL; PnL 7× UAC, 13×
UTL. No obvious "should-be-UAC" event-schema classes redefined.

### Locally-defined types worth UAC promotion review (Phase 1 — likely 0 PRs)

| Source repo                        | File / Class                                                                                                                                                                                                                                                                                      | Provenance comment in source                                                 | Phase 1 decision                                                                                                                                                                                |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `risk-and-exposure-service`        | `models.py` :: `RiskLimits(BaseModel)`                                                                                                                                                                                                                                                            | `# CORRECT-LOCAL: service-internal config model, not a domain data contract` | KEEP local (lands in `strategy_service/risk/models.py`)                                                                                                                                         |
| `position-balance-monitor-service` | `models.py` :: `ReconciliationSummaryDict`, `TriggerReconciliationResponseDict` (TypedDict), `Position`, `LocalFillRecord`, `ReconciliationSnapshot`, `PositionResponse`, `ReconciliationStatusResponse`, `FeeLayerSnapshot`, `FeeReconciliationSnapshot`, `CumulativeFeeDiscrepancy` (BaseModel) | All 10 tagged `# CORRECT-LOCAL`                                              | KEEP local (lands in `strategy_service/position/models.py`). External consumer dep: `system-integration-tests/.../test_recon_rebalancing.py` imports `ReconciliationSnapshot` → rewrite in (b). |
| `position-balance-monitor-service` | `v2/records.py` :: `V2Fill`, others                                                                                                                                                                                                                                                               | Used by `e2e-testing` integration test                                       | KEEP local; (b) rewrite handles external consumer                                                                                                                                               |
| `position-balance-monitor-service` | `core/treasury_monitor.py` :: `TreasuryConfig`, `TreasuryMonitor`, `WalletConfig`                                                                                                                                                                                                                 | Used by `deployment-api` + `e2e-testing`                                     | KEEP local; (b) rewrite handles external consumers                                                                                                                                              |
| `pnl-attribution-service`          | `engine/types.py` + 3 dataclasses                                                                                                                                                                                                                                                                 | Internal engine types                                                        | KEEP local                                                                                                                                                                                      |

Each source repo already audited (comment markers like `# CORRECT-LOCAL` are present), suggesting a prior SSOT sweep
landed. **Phase 1 decision: N/A. No UAC PRs needed.**

### Kill-switch event taxonomy (callout)

Each source repo has a `kill_switch_bus_subscriber.py` file. They all consume the UAC `KillSwitchBusEvent` schema from
`unified_api_contracts` (verified by grep — no local enum redefinition). The subscribers wire to the same UTL
`ServiceBootstrap(kill_switch_subscriber=...)` hook. This is HEALTHY — no taxonomy lift needed. See § (f) for the
boilerplate-lift candidate.

---

## (f) Cross-package helper duplication (lift-to-UTL candidates)

| File (path within package)      | risk | pbm | pnl    | strategy                     | LOC range    | Lift candidate?                                                                                                                                                                                          |
| ------------------------------- | ---- | --- | ------ | ---------------------------- | ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `auth_s2s.py`                   | 71   | 5   | 5      | absent                       | 5–71         | NO — PBM/PnL are 5-LOC stubs; risk's 71-LOC is the real impl. KEEP risk's version, drop the 2 stubs at Phase 4.                                                                                          |
| `config_reloaders.py`           | 152  | 112 | 112    | 312                          | 112–312      | **YES** — typed-class scaffolding pattern repeats 4×. Phase 5 candidate: lift `make_config_reloader(config_cls)` helper into UTL. STEP 5.34 already enforces typed class.                                |
| `isolation_policy.py`           | 93   | 97  | 86     | absent                       | 86–97        | **MAYBE** — 3-way duplication, ~90 LOC each. Likely same pattern: `isolation_for(asset_group)` factory. Phase 5 lift if diff < 30%.                                                                      |
| `kill_switch_bus_subscriber.py` | yes  | yes | yes    | yes                          | ~80–100 each | **YES** — 4-way duplication of the same ServiceBootstrap wiring + KillSwitchBus event handler. Phase 5: lift `make_kill_switch_subscriber(on_fire, on_clear)` into UTL. Each call-site shrinks to 5 LOC. |
| `metrics.py`                    | yes  | yes | yes    | yes                          | (varies)     | NO direct lift — service-specific metric names. Each lands in its sub-package; OK as duplication.                                                                                                        |
| `models.py`                     | yes  | yes | absent | absent (has `models/` dir)   | (varies)     | NO lift — internal/local models per § (e).                                                                                                                                                               |
| `__main__.py`                   | yes  | yes | yes    | yes                          | trivial      | DROP — Phase 4 unifies via single `strategy_service/__main__.py`.                                                                                                                                        |
| `cli/main.py`                   | yes  | yes | yes    | yes (`cli/service_entry.py`) | (varies)     | DROP source `cli/main.py`'s — Phase 4 unifies via `--operation` dispatcher in strategy-service's `cli/main.py`.                                                                                          |
| `api/main.py`                   | yes  | yes | yes    | yes                          | (varies)     | MERGE — Phase 4 (c) collapses 4× `make_health_router(...)` calls into one aggregated router with sub-paths `/health/{risk,position,pnl,strategy}`.                                                       |

### ServiceBootstrap callsites

| Repo                               | File:line                  | Wiring                                                      |
| ---------------------------------- | -------------------------- | ----------------------------------------------------------- |
| `risk-and-exposure-service`        | `cli/main.py:195`          | `ServiceBootstrap(... kill_switch_subscriber=on_bus_event)` |
| `position-balance-monitor-service` | `cli/main.py:124`          | `ServiceBootstrap(... kill_switch_subscriber=on_bus_event)` |
| `pnl-attribution-service`          | `cli/main.py:183`          | `ServiceBootstrap(... kill_switch_subscriber=on_bus_event)` |
| `strategy-service`                 | `cli/service_entry.py:759` | `ServiceBootstrap(... kill_switch_subscriber=...)`          |

Phase 4 (e) consolidates these into ONE top-level `ServiceBootstrap` call. Per-surface kill-switch subscribers can
either (a) all wire into a single composite subscriber that fans out, or (b) keep per-sub-package subscribers and
register them all via a list passed to `ServiceBootstrap` (UTL would need to accept a list). **Lean recommendation:
composite fan-out wrapper (no UTL change)**.

### ManifestFreshnessCache adoption

`rg "ManifestFreshnessCache"` across all 4 repos → **0 hits**. Neither the source repos nor strategy-service have
adopted ManifestFreshnessCache yet. Per CLAUDE.md memory file, this was a P1 bug in MTDS that was already fixed there.
NOT IN SCOPE for this consolidation. **Phase 5 N/A.**

---

## (g) Per-repo `pyproject.toml` dependency union — conflicts + resolution

### Deps union (alphabetised, pinning conflicts flagged)

| Dep                                        | risk               | pbm                                       | pnl                | strategy           | Conflict?                                  | Resolution                                                    |
| ------------------------------------------ | ------------------ | ----------------------------------------- | ------------------ | ------------------ | ------------------------------------------ | ------------------------------------------------------------- |
| `aiofiles`                                 | `>=24.1.0,<25.0.0` | `>=24.1.0,<25.0.0`                        | —                  | —                  | none                                       | KEEP `>=24.1.0,<25.0.0`                                       |
| `aiohttp`                                  | `>=3.13.4,<4.0.0`  | `>=3.13.4,<4.0.0`                         | `>=3.13.4,<4.0.0`  | `>=3.13.4,<4.0.0`  | none                                       | KEEP                                                          |
| `bandit`                                   | `>=1.7.0,<2.0.0`   | `>=1.7.0,<2.0.0`                          | `>=1.7.0,<2.0.0`   | `>=1.7.0,<2.0.0`   | none                                       | KEEP                                                          |
| `basedpyright`                             | `==1.38.2`         | `==1.38.2`                                | `==1.38.2`         | `==1.38.2`         | none                                       | KEEP                                                          |
| `binance-futures-connector`                | —                  | —                                         | —                  | `>=2.0.0,<3.0.0`   | none                                       | KEEP                                                          |
| `cryptography`                             | —                  | —                                         | `>=46.0.7,<47.0.0` | `>=46.0.7,<47.0.0` | none                                       | KEEP                                                          |
| `fastapi`                                  | `>=0.115.0,<1.0.0` | `>=0.115.0,<1.0.0`                        | `>=0.115.0,<1.0.0` | —                  | NEW for strategy                           | ADD `>=0.115.0,<1.0.0`                                        |
| `gcloud-aio-storage`                       | —                  | —                                         | —                  | `>=9.0.0,<10.0.0`  | strategy-only                              | KEEP                                                          |
| `google-cloud-firestore`                   | —                  | —                                         | —                  | `>=2.19.0,<3.0.0`  | strategy-only                              | KEEP                                                          |
| `httpx`                                    | —                  | `>=0.28.1,<1.0.0`                         | —                  | —                  | none                                       | ADD                                                           |
| `market-tick-data-service`                 | —                  | `>=0.1.0,<1.0.0` (editable via uv source) | —                  | —                  | **PBM-only** — depends on MTDS as editable | KEEP `[tool.uv.sources.market-tick-data-service]` + dep entry |
| `matplotlib`                               | —                  | —                                         | —                  | `>=3.9.0,<4.0.0`   | strategy-only                              | KEEP                                                          |
| `mypy`                                     | `>=1.13.0,<2.0.0`  | `>=1.13.0,<2.0.0`                         | —                  | —                  | none                                       | ADD                                                           |
| `numba`                                    | —                  | —                                         | —                  | `>=0.62.1,<1.0.0`  | strategy-only                              | KEEP                                                          |
| `numpy`                                    | —                  | —                                         | `>=2.3.0,<2.4.0`   | `>=2.3.0,<2.4.0`   | none                                       | KEEP                                                          |
| `opentelemetry-*` (api/sdk/exporter/instr) | `>=1.27.0,<2.0.0`  | —                                         | —                  | `>=1.27.0,<2.0.0`  | none                                       | KEEP                                                          |
| `pandas`                                   | `>=2.3.0,<3.0.0`   | `>=2.3.0,<3.0.0`                          | `>=2.3.0,<3.0.0`   | `>=2.3.0,<3.0.0`   | none                                       | KEEP                                                          |
| `pandas-stubs`                             | —                  | `>=2.2.0,<3.0.0`                          | `>=2.2.0,<3.0.0`   | `>=2.2.0,<3.0.0`   | none                                       | KEEP                                                          |
| `pillow`                                   | —                  | —                                         | —                  | `>=12.2.0,<13.0.0` | strategy-only                              | KEEP                                                          |
| `pip-audit`                                | `>=2.7.0,<3.0.0`   | `>=2.7.0,<3.0.0`                          | `>=2.7.0,<3.0.0`   | `>=2.7.0,<3.0.0`   | none                                       | KEEP                                                          |
| `plotly`                                   | —                  | —                                         | —                  | `>=6.4.0,<7.0.0`   | strategy-only                              | KEEP                                                          |
| `polars`                                   | —                  | —                                         | —                  | `>=1.37.0,<2.0.0`  | strategy-only                              | KEEP                                                          |
| `pre-commit`                               | —                  | —                                         | `>=3.0,<4.0.0`     | —                  | pnl-only (legacy; use `prek` instead)      | **DROP** — replace with `prek` ≥0.3.0 (others use it)         |
| `prek`                                     | `>=0.3.0,<1.0.0`   | `>=0.3.0,<1.0.0`                          | —                  | —                  | pnl uses pre-commit; risk/pbm use prek     | UNIFY → `prek>=0.3.0,<1.0.0`                                  |
| `prometheus-client`                        | `>=0.20.0,<1.0.0`  | `>=0.20.0,<1.0.0`                         | `>=0.20.0,<1.0.0`  | `>=0.20.0,<1.0.0`  | none                                       | KEEP                                                          |
| `psutil`                                   | `>=6.0.0,<7.0.0`   | `>=6.0.0,<7.0.0`                          | `>=6.0.0,<7.0.0`   | `>=6.0.0,<7.0.0`   | none                                       | KEEP                                                          |
| `psycopg2-binary`                          | —                  | `>=2.9.9,<3.0.0`                          | —                  | —                  | PBM-only (SQLAlchemy/Postgres)             | ADD                                                           |
| `pydantic`                                 | `>=2.12.5,<3.0.0`  | `>=2.12.5,<3.0.0`                         | (transitive)       | `>=2.12.5,<3.0.0`  | none                                       | KEEP                                                          |
| `pydantic-settings`                        | `>=2.12.0,<3.0.0`  | `>=2.12.0,<3.0.0`                         | (transitive)       | `>=2.12.0,<3.0.0`  | none                                       | KEEP                                                          |
| `pygments`                                 | `>=2.20.0,<3.0.0`  | `>=2.20.0,<3.0.0`                         | `>=2.20.0,<3.0.0`  | `>=2.20.0,<3.0.0`  | none                                       | KEEP                                                          |
| `pyjwt`                                    | `>=2.12.0,<3.0.0`  | `>=2.12.0,<3.0.0`                         | `>=2.12.0,<3.0.0`  | `>=2.12.0,<3.0.0`  | none                                       | KEEP                                                          |
| `pytest`                                   | `>=9.0.3,<10.0.0`  | `>=9.0.3,<10.0.0`                         | `>=9.0.3,<10.0.0`  | `>=9.0.3,<10.0.0`  | none                                       | KEEP                                                          |
| `pytest-asyncio`                           | `>=0.25.0,<2.0.0`  | `>=0.25.0,<2.0.0`                         | `>=0.25.0,<2.0.0`  | `>=0.25.0,<2.0.0`  | none                                       | KEEP                                                          |
| `pytest-cov`                               | `>=7.0.0,<8.0.0`   | `>=7.0.0,<8.0.0`                          | `>=7.0.0,<8.0.0`   | `>=7.0.0,<8.0.0`   | none                                       | KEEP                                                          |
| `pytest-mock`                              | —                  | `>=3.15.0,<4.0.0`                         | —                  | `>=3.15.0,<4.0.0`  | none                                       | KEEP                                                          |
| `pytest-socket`                            | `>=0.7.0,<1.0.0`   | `>=0.7.0,<1.0.0`                          | `>=0.7.0,<1.0.0`   | `>=0.7.0,<1.0.0`   | none                                       | KEEP                                                          |
| `pytest-timeout`                           | `>=2.4.0,<3.0.0`   | `>=2.4.0,<3.0.0`                          | `>=2.4.0,<3.0.0`   | `>=2.4.0,<3.0.0`   | none                                       | KEEP                                                          |
| `pytest-xdist`                             | `>=3.6.0,<4.0.0`   | `>=3.6.0,<4.0.0`                          | `>=3.6.0,<4.0.0`   | `>=3.6.0,<4.0.0`   | none                                       | KEEP                                                          |
| `python-dotenv`                            | —                  | —                                         | `>=1.2.2,<2.0.0`   | —                  | pnl-only                                   | ADD if any pnl module uses it; otherwise drop                 |
| `python-dateutil`                          | —                  | —                                         | —                  | `>=2.8.2,<3.0.0`   | strategy-only                              | KEEP                                                          |
| `python-multipart`                         | —                  | `>=0.0.27,<1.0.0`                         | —                  | —                  | PBM-only (FastAPI form parsing)            | ADD                                                           |
| `pyyaml`                                   | —                  | —                                         | —                  | `>=6.0.1,<7.0.0`   | strategy-only                              | KEEP                                                          |
| `requests`                                 | `>=2.33.0,<3.0.0`  | `>=2.33.0,<3.0.0`                         | `>=2.33.0,<3.0.0`  | (transitive)       | none                                       | KEEP                                                          |
| `responses`                                | —                  | —                                         | —                  | `>=0.24.1,<1.0.0`  | strategy-only (test mocking)               | KEEP                                                          |
| `rich`                                     | —                  | —                                         | —                  | `>=14.2.0,<15.0.0` | strategy-only                              | KEEP                                                          |
| `ruff`                                     | `==0.15.0`         | `==0.15.0`                                | `==0.15.0`         | `==0.15.0`         | none                                       | KEEP                                                          |
| `scipy`                                    | —                  | —                                         | `>=1.15.0,<2.0.0`  | —                  | **pnl-only — adds heavy dep**              | ADD `>=1.15.0,<2.0.0`                                         |
| `slowapi`                                  | —                  | `>=0.1.9,<1.0.0`                          | —                  | —                  | PBM-only (rate limiting)                   | ADD                                                           |
| `sqlalchemy`                               | —                  | `>=2.0.0,<3.0.0`                          | —                  | —                  | PBM-only                                   | ADD                                                           |
| `sse-starlette`                            | `>=1.6.1,<2.0.0`   | `>=1.6.1,<2.0.0`                          | —                  | `>=1.6.1,<2.0.0`   | none                                       | KEEP                                                          |
| `starlette`                                | —                  | `>=0.52.1,<1.0.0`                         | —                  | —                  | PBM (FastAPI sub-dep)                      | ADD                                                           |
| `typer`                                    | —                  | —                                         | —                  | `>=0.9.0,<1.0.0`   | strategy-only                              | KEEP                                                          |
| `types-requests`                           | —                  | `>=2.32.0,<3.0.0`                         | —                  | `>=2.32.0,<3.0.0`  | none                                       | KEEP                                                          |
| `unified-api-contracts`                    | `>=0.1.0,<1.0.0`   | `>=0.1.0,<1.0.0`                          | `>=0.1.0,<1.0.0`   | `>=0.1.0,<1.0.0`   | none                                       | KEEP                                                          |
| `unified-trading-library`                  | `>=0.1.0,<1.0.0`   | `>=0.1.0,<1.0.0`                          | `>=0.1.0,<1.0.0`   | `>=0.3.0,<1.0.0`   | **CONFLICT** — strategy wants ≥0.3.0       | **Resolve to `>=0.3.0,<1.0.0`** (latest floor wins)           |
| `urllib3`                                  | —                  | —                                         | `>=2.7.0,<3.0.0`   | —                  | pnl-only                                   | ADD (transitive of requests; pin is fine)                     |
| `uvicorn[standard]`                        | `>=0.27.0,<1.0.0`  | `>=0.27.0,<1.0.0`                         | `>=0.29.0,<1.0.0`  | —                  | **mild** — pnl wants ≥0.29.0               | **Resolve to `>=0.29.0,<1.0.0`** (latest floor wins)          |

### Conflict summary

- `unified-trading-library`: strategy `>=0.3.0` vs others `>=0.1.0` → unified to `>=0.3.0,<1.0.0`.
- `uvicorn[standard]`: pnl `>=0.29.0` vs others `>=0.27.0` → unified to `>=0.29.0,<1.0.0`.
- `pre-commit` (pnl-only) vs `prek` (risk + PBM) → **drop `pre-commit`, unify on `prek>=0.3.0,<1.0.0`**.
- Editable `tool.uv.sources.market-tick-data-service` MUST be retained in the merged pyproject (PBM needs it for
  `defi_health_aggregator.py` etc.).
- Everything else is a clean union with no conflicts.

### `[project.scripts]` union

| Existing entry               | Source repo      | Post-merge handling                                               |
| ---------------------------- | ---------------- | ----------------------------------------------------------------- |
| `strategy-service = ...`     | strategy-service | KEEP                                                              |
| `risk-monitor = ...`         | risk             | DROP — folded into `strategy-service --operation risk-monitor`    |
| `position-monitor = ...`     | PBM              | DROP — folded into `strategy-service --operation position-recon`  |
| `position-monitor-std = ...` | PBM              | DROP                                                              |
| `pnl-attribution = ...`      | pnl              | DROP — folded into `strategy-service --operation pnl-attribution` |
| `pnl-attribution-std = ...`  | pnl              | DROP                                                              |

**Operator-impact callout**: any launcher / cron / shell script invoking `risk-monitor` / `position-monitor` /
`pnl-attribution` as a console script will break post-archive. Phase 8A covers launcher migration; Phase 0 (h) below
lists the hardcoded uses.

---

## (h) Hardcoded service-name strings

Counts (workspace-wide, source-repo internal hits excluded) for each hyphenated name:

| Name                               | Total hits | Top consumer (by file count)                                  |
| ---------------------------------- | ---------- | ------------------------------------------------------------- |
| `risk-and-exposure-service`        | 1562       | unified-trading-pm (329 hits), unified-trading-system-ui (68) |
| `position-balance-monitor-service` | 1491       | unified-trading-pm (304), unified-trading-system-ui (64)      |
| `pnl-attribution-service`          | 912        | unified-trading-pm (226), unified-trading-system-ui (55)      |

Hits per sibling repo (sorted by traffic):

| Sibling repo                                  | RES | PBM | PnL | Notes                                                                          |
| --------------------------------------------- | --- | --- | --- | ------------------------------------------------------------------------------ |
| `unified-trading-pm`                          | 329 | 304 | 226 | docs / codex / plans / cursor-configs — see below                              |
| `unified-trading-system-ui`                   | 68  | 64  | 55  | DART drilldown UI labels — Phase 8B                                            |
| `unified-api-contracts`                       | 35  | 29  | 19  | UAC docstrings / readme — surface review                                       |
| `deployment-service`                          | 34  | 30  | 26  | Terraform + bucket configs + cloud-build + clusters + launchers — **Phase 8A** |
| `unified-trading-library`                     | 14  | 12  | 7   | UTL docstrings + service-name registry — review                                |
| `execution-service`                           | 13  | 4   | 5   | code comments + leg_controller_runner import (b)                               |
| `e2e-testing`                                 | 12  | 9   | 10  | colocated_engine.py + integration tests (b)                                    |
| `trading-agent-service`                       | 10  | 1   | 1   | agent docstrings                                                               |
| `alerting-service`                            | 10  | 5   | 3   | alert routing / labels                                                         |
| `system-integration-tests`                    | 8   | 6   | 6   | integration tests (b)                                                          |
| `deployment-ui`                               | 6   | 3   | 5   | DART service-list — **Phase 8B**                                               |
| `deployment-api`                              | 6   | 4   | 4   | service registry routes + (b)                                                  |
| `unified-trading-api`                         | 2   | 3   | 1   | umbrella API                                                                   |
| `agent-orchestrator`                          | 2   | 0   | 0   |                                                                                |
| `market-data-processing-service`              | 1   | 0   | 1   | crosslink doc                                                                  |
| `batch-live-reconciliation-service`           | 1   | 1   | 1   | docstrings                                                                     |
| `client-reporting-api`                        | 0   | 2   | 1   |                                                                                |
| `fund-administration-service`                 | 0   | 1   | 0   |                                                                                |
| `strategy-service`                            | 0   | 2   | 7   | code comments (not imports — confirmed (b))                                    |
| `features-service`                            | 0   | 0   | 1   |                                                                                |
| `unified-trading-system-repos.code-workspace` | 1   | 1   | 1   | workspace folder entry — Phase 7 step 4                                        |

### Critical `deployment-service` references (Phase 8A targets)

`deployment-service/cloud-build/refresh-tarballs.cloudbuild.yaml` lines 120, 121, 122 list all 3 services.

`deployment-service/terraform/shared/gcp/main.tf` lines 48, 49, 50 — service registry.

`deployment-service/terraform/cloud-build/gcp/main.tf` lines 91-101 — per-service `github_repo` +
`artifact_registry_repo` map (3 entries).

`deployment-service/terraform/services/{risk-and-exposure-service,position-balance-monitor-service,pnl-attribution-service}/`
— **entire per-service Terraform directories** (variables.tf, main.tf, outputs.tf on both GCP + AWS). Phase 8A must
collapse all three into a parameterised strategy-service module.

`deployment-service/configs/bucket_config.yaml` lines 184-220 (10 entries for risk) +
`deployment-service/configs/clusters/{cefi,defi,full,prediction,sports,tradfi}.yaml` (list members).

`deployment-service/configs/RUNTIME_TOPOLOGY_DECISIONS.md` — 50+ refs; doc-style update.

`deployment-service/scripts/setup-registry.sh:138-150`, `deployment-service/scripts/aws/setup-ecr-repos.sh:54-55`,
`deployment-service/scripts/bootstrap/bootstrap_gcp.sh:204`, `deployment-service/scripts/bootstrap/bootstrap_aws.sh:326`
— service enumeration.

`deployment-service/scripts/vm/create-code-tarballs.sh` lines 59, 69, 77, 83, 105 — tarball builder explicitly
references all 3 (Phase 8A: collapse to strategy-service only).

`deployment-service/scripts/vm/launch-wallet-treasury-cutover-vm.sh` lines 31, 41, 44, 89, 161, 163, 213, 249 —
references PBM script paths (`position-balance-monitor-service/scripts/...`). Phase 8A updates these to
`strategy-service/scripts/position/...`.

`deployment-service/scripts/vm/setup-data-pipeline-vm.sh:200, 204, 229, 233, 279, 280` — code-tarball mapping &
VM-prefix shortform (`pbm`, `pnl`). Decide whether to KEEP shortform prefixes or rename.

`deployment-service/scripts/vm/backfill-cluster.sh` lines 141, 217, 227, 239, 245, 251, 266 — service enumeration for
cluster operations.

`deployment-service/deployment_service/cli/utils/manifest_reader.py:61, 73, 122` — service → bucket naming map
(`risk-and-exposure-service: risk-and-exposure-{project_id}`).

`deployment-service/tests/unit/test_dependencies.py:550` — dependency-order assertion
(`position-balance-monitor-service < risk-and-exposure-service`). Phase 8A drops/rewrites.

`deployment-service/configs/services/risk-and-exposure-service/live.env` etc. — per-service env configs (Phase 8A merges
into strategy-service env or splits by `--operation`).

`deployment-service/uv.lock` lines 694, 731, 2521, 2523 — editable source. Phase 7 dep regen.

`deployment-service/docs/resource-profiles/risk-and-exposure-service.md` + README — resource-profile docs (Phase 9 codex
parallel).

### `unified-trading-pm` references (Phase 9 codex sweep)

432 hits across cursor-configs + codex. Phase 9 must update:

- `cursor-configs/workspace-trading.code-workspace`, `cursor-configs/workspace-complete.code-workspace`,
  `cursor-configs/unified-trading-system-repos.code-workspace` — workspace folder entries (4 tabs × 3 repos = 12 entries
  each).
- `/codex/04-architecture/strategy-service-architecture.md` (already exists — UPDATE per Phase 9 (a)).
- `/codex/04-architecture/runtime-deployment-topology.md` (25 hits across 3 names).
- `/codex/04-architecture/risk-preflight-flow.md`, `/codex/04-architecture/amm-slippage-simulation.md`,
  `codex/04-architecture/deprecation-ledger.yaml`.
- `/codex/00-getting-started/DEPRECATED_SERVICES.md` (PROMOTE the 3 to deprecated).
- `/codex/03-services/venue-capability-registry.md`, `/codex/03-observability/slos.md`.
- `codex/11-project-management/{service-registry.yaml, mvp-universe.yaml, venue-support-matrix.yaml, epics/*.yaml}` —
  service-registry SSOT updates.
- `codex/15-runbooks/*.md` — runbook owner / path references (alerting/position_drift, balance_drift,
  kill_switch_defi_liquidation_risk, kill_switch_portfolio_drawdown, margin_threshold_breach, alert-code-taxonomy,
  position-reconciliation-deploy-gate).
- `codex/10-audit/_service-pipeline-post-trade.yaml`, `codex/10-audit/repos/risk-and-exposure-service.yaml`,
  `codex/10-audit/repos/pnl-attribution-service.yaml`, `codex/10-audit/_archive/live/pnl-attribution-service.yaml`,
  `/codex/10-audit/MASTER_READINESS_LIVE_DEFI_2026_05_23.md`, `/codex/10-audit/consolidation-gap-analysis.md`,
  `/codex/10-audit/CONTRACTS_SEPARATION_AUDIT.md`, `codex/10-audit/epic-checklist-mapping.yaml`,
  `codex/10-audit/validator-epic-mapping.yaml`, `/codex/10-audit/FOUNDATIONAL-REPOS-AUDIT-2026-03-07.md`.
- `codex/05-infrastructure/unified-libraries/{LIBRARY-DEPENDENCY-MATRIX.md, INTERNAL_DEPENDENCY_GRAPH.md}`.
- `codex/06-coding-standards/{integration-testing-layers.md, dependency-management.md, quality-gates.md}`.
- `/codex/09-strategy/architecture-v2/cross-cutting/restaking-reward-economics.md`.
- `/codex/13-codex-governance/SSOT-BOUNDARY.md`, `/codex/10-audit/README.md`.

### Env-var prefixes (`RISK_AND_EXPOSURE_SERVICE_*` etc.)

**ZERO** hits outside the plan body itself. None of the source repos use shouty-case env prefixes in code.
Strategy-service uses `STRATEGY_SERVICE_*` envs (verified) — no rename required.

Grep:

```bash
rg -F "RISK_AND_EXPOSURE_SERVICE" -g '!.venv*' --no-ignore-vcs       # 1 hit (plan body itself)
rg -F "POSITION_BALANCE_MONITOR_SERVICE" -g '!.venv*' --no-ignore-vcs # 0 hits
rg -F "PNL_ATTRIBUTION_SERVICE" -g '!.venv*' --no-ignore-vcs          # 0 hits
```

### Console-script command names (used in launchers / cron / docs)

- `risk-monitor` — defined by risk pyproject; consumer: launchers / docs. Phase 8A audit.
- `position-monitor` / `position-monitor-std` — PBM pyproject; consumer: launchers / docs.
- `pnl-attribution` / `pnl-attribution-std` — pnl pyproject; consumer: launchers / docs.

After consolidation:
`python -m strategy_service --operation {risk-monitor,position-recon,pnl-attribution,strategy-batch,strategy-live,backtest}`.

### Pub/sub topic prefixes

Not directly inspected per-repo. Recommend Phase 0 follow-up grep:

```bash
rg -nF -e "risk-and-exposure-service" -e "position-balance-monitor-service" -e "pnl-attribution-service" \
  unified-api-contracts/ unified-trading-library/ \
  | grep -iE "topic|publish|subscribe|pubsub"
```

Per CLAUDE.md "Live = batch" rule, topic-name compatibility (rename vs keep-legacy-prefix-for-subscribers) is a P0
decision before Phase 3. **Recommendation: KEEP legacy topic prefixes** (`risk-monitor.*`, `position-monitor.*`,
`pnl-attribution.*`) for first 7 days post-cutover to avoid double-rebind race; rename in a follow-up after archive
lands. Add named-successor plan.

---

## Summary + recommendations

1. **(b) is the headline finding**: 25 external import statements across 7 files in 5 sibling repos. Fact-report
   2026-05-19 said ZERO. **Plan Phase 4 (a) sed-rewrite scope expands by ~7 files**:
   `deployment-api/deployment_api/routes/treasury_routes.py`,
   `execution-service/execution_service/algo_library/leg_controller_runner.py`,
   `e2e-testing/scripts/defi/colocated_engine.py`, `e2e-testing/tests/integration/test_architecture_v2_roundtrip.py`,
   `system-integration-tests/tests/integration/test_recon_rebalancing.py`,
   `system-integration-tests/tests/integration/test_phase6_reward_realisation_e2e.py`,
   `system-integration-tests/tests/integration/test_leveraged_leg_controller_e2e.py`,
   `system-integration-tests/tests/smoke/test_sports_arb_pipeline.py`. The two non-test consumers (deployment-api
   treasury route + execution-service leg controller) are PRODUCTION CODE PATHS. The
   `e2e-testing/scripts/defi/colocated_engine.py` consumer is the **primary May-23 promote-CLI path** per CLAUDE.md.

2. **(a) architectural collision**: `strategy_service/models/` already contains `position.py` + `pnl.py`. Post-merge,
   `strategy_service/position/models.py` + `strategy_service/pnl/...` will coexist with the existing
   `strategy_service/models/{position,pnl}.py`. Symbols don't collide but the layout is confusing. P1 follow-up — not
   cutover-blocking.

3. **(e + § (f))**: kill-switch event taxonomy is already UAC-canonical (no local enum redefinitions); the **subscriber
   boilerplate** is duplicated 4× and is a clean UTL lift candidate for Phase 5. ManifestFreshnessCache is NOT in scope
   — none of the 4 repos have adopted it yet.

4. **(g) pyproject conflicts**: 3 minor resolutions needed (`unified-trading-library>=0.3.0`, `uvicorn>=0.29.0`,
   `prek>=0.3.0` displacing pnl's `pre-commit`). Editable `[tool.uv.sources.market-tick-data-service]` must be retained.

5. **(h) deployment-service blast radius**: 90+ hits across Terraform (6 per-service dirs on GCP + AWS), cloud-build,
   cluster configs, bucket configs, launchers, bootstrap scripts. Phase 8A is the largest single-repo edit in the plan.
   Many touch infrastructure-as-code that's been `terraform apply`'d — Phase 8A should plan for `terraform destroy` of
   the 3 service modules in conjunction with `terraform apply` of the updated strategy-service module.

6. **No `risk-and-exposure-service` / `position-balance-monitor-service` / `pnl-attribution-service` imports inside
   strategy-service itself** (verified) — only narrative comments. Confirms subtree-merge has zero compile-time
   collisions WITHIN strategy-service. The 7 external-consumer files are the only blast radius for Phase 4 sed.

7. **CLAUDE.md `try/except ImportError` violations** present in
   `system-integration-tests/tests/smoke/test_sports_arb_pipeline.py` and elsewhere — Phase 4 should remove these guards
   post-rewrite (the imports become unconditional intra-package).

8. **`strategy-service/strategy_service/engine/position_client.py` + several v2 strategies** carry narrative comments
   like "forwards to pnl-attribution-service". These are doc-comments only (no import). Phase 9 docstring sweep should
   update to "forwards to `strategy_service.pnl.*`".

9. **PYTEST_UNIT_DIR override**: PBM's deep `tests/position_interface/unit/` test tree triggers the override trigger
   from CLAUDE.md. Phase 4 (g) MUST add `PYTEST_UNIT_DIR="tests/"` to strategy-service's `quality-gates.sh` BEFORE
   sourcing `base-service.sh`, or PBM's interface tests silently skip.

10. **Console-script entries**: 5 obsolete `[project.scripts]` entries (`risk-monitor`, `position-monitor`,
    `position-monitor-std`, `pnl-attribution`, `pnl-attribution-std`) get folded into
    `strategy-service --operation <op>`. Phase 8A must audit launchers / cron / docs for direct command-line use of
    these names.
