---
scope: [engineer, admin]
status: stable
last_reviewed: 2026-05-20
---

# strategy-service architecture

> **Consolidation complete (2026-05-20).** The 3 predecessor repos (`risk-and-exposure-service`,
> `position-balance-monitor-service`, `pnl-attribution-service`) have been subtree-merged into `strategy-service` as
> sub-packages (`strategy_service/risk/`, `/position/`, `/pnl/`). Phase 6 parity gate: 4059 passed, 316 skipped, 0
> errors. Phase 8A launcher migration landed at deployment-service@7679dfe + @2ed3fdd. See
> [`strategy_repo_consolidation_2026_05_19`](../../plans/active/strategy_repo_consolidation_2026_05_19.md) for full
> migration history. Mirrors the `features-service-architecture.md` template.

## TL;DR

Four previously-separate workspace repos consolidated into a single [`strategy-service`](../../../strategy-service/)
repo with sub-packages per surface. ONE Docker image, ONE [`pyproject.toml`](../../../strategy-service/pyproject.toml),
ONE Health-API aggregator, ONE CLI dispatcher parameterised by `--operation`. Subtree-merged with full per-repo git
history preserved. The 3 monitoring-service predecessors (`risk-and-exposure-service`,
`position-balance-monitor-service`, `pnl-attribution-service`) are archived post-merge; new code lands in
`strategy-service` only.

This consolidation is pre-requisite for the 2026-05-23 live-DeFi cutover topology — paper trading, live trading, batch
backtest, risk monitoring, position reconciliation, and PnL attribution are colocated activities on the same VM in
deployment. Maintaining 4 separate image build + deploy pipelines against that topology is operationally infeasible.

## Sub-package layout

```
strategy-service/
├── strategy_service/
│   ├── __init__.py
│   ├── __main__.py                     # python -m strategy_service entry-point
│   ├── api/main.py                     # Health-API aggregator: /health/{risk,position,pnl,strategy}
│   ├── cli/main.py                     # dispatcher: parses --operation, forwards rest
│   ├── config_reloaders.py             # single typed StrategyServiceConfig root, sub-namespaces per surface
│   ├── common/                         # cross-surface lifts (Phase 5 helpers from UTL)
│   ├── engine/                         # existing strategy core (unchanged)
│   │   ├── core/                       # data provider, cloud storage, signal assembly, config loading
│   │   ├── strategies/v2/              # 12+ V2 strategy classes
│   │   ├── backtest/
│   │   ├── futures/
│   │   └── lifecycle/
│   ├── portfolio_allocator/            # existing (unchanged)
│   ├── signal_broadcast/               # existing (unchanged)
│   ├── validation/                     # existing (unchanged)
│   ├── version_governance/             # existing (unchanged)
│   ├── risk/                           # was risk-and-exposure-service/
│   │   ├── core/                       # alert_manager, risk_calculator, position_monitor_client
│   │   ├── engine/                     # orchestrator, mock data provider
│   │   └── v2/                         # margin_sim, orchestrator, preflight
│   ├── position/                       # was position-balance-monitor-service/
│   │   ├── core/                       # 13 modules — balance/pnl/position/nav/fee reconciliation
│   │   ├── storage/                    # database + position_store
│   │   └── v2/                         # attribution, invariants, projections
│   └── pnl/                            # was pnl-attribution-service/
│       ├── engine/                     # breakdown, archetype_aggregator, sports_pnl, reward_attribution_drain
│       ├── analytics/
│       └── execution_alpha/
├── pyproject.toml                      # ONE flat dependency list (no optional groups)
├── Dockerfile                          # ONE image
├── scripts/{risk,position,pnl,strategy}/
└── tests/{risk,position,pnl,strategy}/
```

## CLI dispatch

`--operation` is the discriminator; existing per-surface flags preserved verbatim post-merge:

| Operation         | Mode         | Previous repo                    | Notes                                                      |
| ----------------- | ------------ | -------------------------------- | ---------------------------------------------------------- |
| `risk-monitor`    | live         | risk-and-exposure-service        | breaker-trip events; ObservedEvent emission per breaker    |
| `position-recon`  | batch / live | position-balance-monitor-service | balance + PnL + fee reconciliation; NAV snapshot           |
| `pnl-attribution` | batch        | pnl-attribution-service          | breakdown, archetype aggregation, sports PnL, reward drain |
| `strategy-batch`  | batch        | strategy-service                 | batch backtest run; archetype × strategy matrix            |
| `strategy-live`   | live         | strategy-service                 | paper / live trading; signal broadcast active              |
| `backtest`        | batch        | strategy-service                 | 2yr config-grid backtest harness                           |

All other CLI axes per `codex/06-coding-standards/cli-convention.md`: `--asset-group`, `--mode`, domain-specific flags.

## Health-API aggregator

`api/main.py` exposes per-surface health under sub-paths:

- `/health/risk` — risk-monitor heartbeat + last-breaker-evaluation freshness
- `/health/position` — position-recon last-run freshness + NAV-snapshot freshness
- `/health/pnl` — pnl-attribution last-run freshness per archetype family
- `/health/strategy` — strategy signal emission freshness + per-V2-strategy heartbeat

Each surface contributes a `data_freshness` callback merged into a single `make_health_router` call.

## ServiceBootstrap consolidation

ONE `ServiceBootstrap` at the consolidated-service top level (STARTED / STOPPED / FAILED at the strategy-service level).
Per-surface sub-bootstraps available for granular kill-switch routing — kill-switch subscriber consolidates the 4 source
repos' `kill_switch_bus_subscriber.py` modules into a single dispatcher keyed by event-type.

## Deployment topology

- ONE Docker image: `asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-library/strategy-service:<sha>`
- ONE VM tarball per asset-group flavor; `--operation` selected at launcher level
- Launcher consolidation: `launch-strategy-vm.sh` parameterised by `--operation` + `--asset-group`. Predecessors
  (`launch-risk-vm.sh`, `launch-position-vm.sh`, `launch-pnl-vm.sh`) deleted.
- Cloud Build refresh-tarballs: single `strategy-service` entry (was 4).
- DART UI service-list: single `strategy-service` entry with 4 health sub-paths.

## Migration history

- 2026-05-19: plan filed
  ([`strategy_repo_consolidation_2026_05_19`](../../plans/active/strategy_repo_consolidation_2026_05_19.md)) — 10-phase
  shape per features-service precedent.
- Pre-cutover race for 2026-05-23 live-DeFi launch; auto-flips to `BLOCKED-CUTOVER` if Phase 6 parity fails.
- Source repos archived via `gh repo archive` post-Phase 6 parity validation:
  - `risk-and-exposure-service` → `strategy_service/risk/`
  - `position-balance-monitor-service` → `strategy_service/position/`
  - `pnl-attribution-service` → `strategy_service/pnl/`

## Cross-references

- [`promote-workflow-architecture.md`](./promote-workflow-architecture.md) — strategy-service is the promote target;
  `--operation` selection drives paper vs live vs batch.
- [`flash-loan-receiver.md`](./flash-loan-receiver.md) — risk/preflight surface in `strategy_service/risk/v2/` consumes
  Aave flash-loan capability declarations.
- [`codex/09-strategy/operational/cli-promote-paths.md`](../09-strategy/operational/cli-promote-paths.md) — promote-CLI
  invokes `strategy-service --operation strategy-live`.
- [`codex/05-infrastructure/launcher-script-ssot.md`](../05-infrastructure/launcher-script-ssot.md) — 4-to-1 launcher
  collapse.
- [`codex/05-infrastructure/vm-tarball-deployment.md`](../05-infrastructure/vm-tarball-deployment.md) — single
  strategy-service tarball replaces 4-source-repo matrix.

## Anti-patterns (do NOT)

- Do NOT re-introduce per-surface repos (risk / position / pnl as separate services). The consolidation was driven by
  operational topology — same VM, same image, same lifecycle.
- Do NOT add asset-group-specific risk / position / pnl variants. `--asset-group` is a CLI axis, not a package-layout
  axis.
- Do NOT split strategy-batch and strategy-live into separate repos. They share 99% of the code path; the only
  difference is execution fills (live vs simulated). Per CLAUDE.md "Batch = Live" HARD RULE.
- Do NOT define event taxonomies locally in `strategy_service/risk/` etc. — all event types live in UAC under
  `unified_api_contracts.canonical.crosscutting.lifecycle` or the appropriate domain bucket.
