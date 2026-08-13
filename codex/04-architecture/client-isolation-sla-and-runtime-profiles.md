---
doc_type: codex-ssot
title: Client Isolation, SLA Tiers, and Runtime Profiles — SSOT
summary:
  "SSOT for runtime-topology v7: per-service isolation (shared/isolated as a choice), SLA tiers
  (basic/standard/premium), runtime profiles (backtest/paper/mock-live/staging/prod replacing 5 mode env vars), and the
  8-point chaos-injection contract."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [alerting-service, client-reporting-api, deployment-api, deployment-service, deployment-ui, e2e-testing]
scope: [engineer, admin]
tags: [client-isolation, sla-tiers, runtime-profiles, chaos, topology, deployment]
related:
  [
    /codex/04-architecture/runtime-deployment-topology.md,
    /codex/05-infrastructure/runtime-tiers-and-deployment.md,
    /codex/09-strategy/architecture-v2/README.md,
  ]
created: 2026-04-17
authoritative_for: [per-service client isolation policy, client SLA tiers, runtime profiles, chaos-injection contract]
referenced_by:
  [
    /codex/04-architecture/runtime-deployment-topology.md,
    /codex/05-infrastructure/runtime-tiers-and-deployment.md,
    /codex/09-strategy/architecture-v2/README.md,
    /codex/14-customer-journeys/environments/README.md,
    /codex/14-customer-journeys/environments/production-odum-research-com.md,
    /codex/14-customer-journeys/playbook-concepts/fund-org-hierarchy.md,
  ]
owner:
last_reviewed: 2026-09-20
code_refs:
---

# Client Isolation, SLA Tiers, and Runtime Profiles — SSOT

**Status:** Active **Paired machine SSOT:** `unified-trading-pm/configs/runtime-topology.yaml` (v7) **Paired UAC
schemas:** `unified_api_contracts.internal.domain.deployment_service.isolation` **Paired UTL reader:**
`unified_trading_library.topology.topology_reader` **Consumers:** deployment-service, deployment-api, deployment-ui,
strategy-service, execution-service, position-balance-monitor-service, risk-and-exposure-service,
pnl-attribution-service, alerting-service

This doc is the single source of truth for four concepts introduced in runtime-topology v7:

1. **Per-service isolation policy** — shared vs isolated, as a _choice_ not a decree.
2. **SLA tiers** — premium / standard / basic, with cost passthrough.
3. **Runtime profiles** — the one axis that replaces the five legacy mode env vars.
4. **Chaos injection hooks** — the contract between the chaos layer and the services it touches.

---

## 1. Why per-service isolation is a choice

The v6 model was binary: shared (L1-L4) vs client-specific (L5-L6). That's too coarse.

Two clients on the same SLA tier can have different needs:

- Client A's bespoke execution is latency-critical → they want `execution-service` dedicated.
- Client A's position tracking is not differentiating → they happily pool with others for cheaper support.

So isolation is per-service, with three axes:

| Axis         | Owner                    | Example                                                                     |
| ------------ | ------------------------ | --------------------------------------------------------------------------- |
| **Default**  | Platform (topology yaml) | execution-service defaults to `isolated`; PBM defaults to `shared`          |
| **Allowed**  | Platform (topology yaml) | PBM allows `[shared, isolated]`; instruments-service allows `[shared]` only |
| **Override** | Client subscription      | Premium client A overrides PBM to `isolated`                                |

The client's ability to override is gated by their **SLA tier's `allowed_isolations`**. Basic clients cannot choose
`isolated` on any service. Premium clients can choose `isolated` on any service that declares it in `allowed`.

## 2. Typical isolation pattern

| Layer | Services                      | Typical isolation                              | Reason                                                                            |
| ----- | ----------------------------- | ---------------------------------------------- | --------------------------------------------------------------------------------- |
| L1    | instruments, market-tick-data | `shared` only                                  | Reference + market data is universal; no client dimension exists.                 |
| L2    | market-data-processing        | `shared` only                                  | Candle aggregation is universal.                                                  |
| L3    | features-\*                   | `shared` only                                  | Features are universal inputs.                                                    |
| L4    | ML training + inference       | `shared` default; inference `isolated` allowed | Bespoke models + dedicated hardware for premium.                                  |
| L5    | **strategy-service**          | `shared` default; `isolated` allowed           | MM / latency-critical archetypes demand isolated + co-located.                    |
| L5    | **execution-service**         | `isolated` only                                | Per-client venue API keys, rate limits, entitlements, order-flow confidentiality. |
| L6    | position, risk, pnl, alerting | `shared` default; `isolated` allowed           | Shared is cheaper and enables cross-client recon; premium can isolate.            |

**Rule:** `execution-service` is the one service that is ALWAYS isolated, regardless of SLA tier. It is the one place
where per-client credentials, per-client rate limits, and per-client order flow cannot be safely multiplexed.

## 3. SLA tiers

| Tier     | Cost multiplier | Min isolated services          | Latency budget | Support SLA |
| -------- | --------------- | ------------------------------ | -------------- | ----------- |
| basic    | 1.0×            | —                              | 500 ms         | 24 h        |
| standard | 2.5×            | execution-service              | 150 ms         | 4 h         |
| premium  | 6.0×            | execution, strategy, PBM, risk | 40 ms          | 30 min      |

`min_isolated_services` forces the listed services to `isolated` at that tier, overriding the service's default. A
standard-tier client doesn't get a choice on execution-service (it's always isolated for them); a premium-tier client
gets a guarantee that strategy+PBM+risk are also dedicated.

**Cost passthrough model** (metadata today; billing wired in a later plan):

- Each isolated service incurs `cost_multiplier × base_cost_per_instance`.
- `client-reporting-api` will pick these up per billing cycle.
- Additional services isolated beyond `min_isolated_services` are billed as line-item deltas.

## 4. Runtime profiles (single axis)

Five env vars were doing one job. v7 collapses them.

| Profile     | cloud_mock_mode | mock_state_mode | auth_disabled | chaos_allowed | real venue calls |
| ----------- | --------------- | --------------- | ------------- | ------------- | ---------------- |
| `backtest`  | false           | deterministic   | true          | **yes**       | no               |
| `paper`     | false           | interactive     | false         | no            | no               |
| `mock-live` | true            | interactive     | true          | yes           | no               |
| `staging`   | false           | interactive     | false         | yes           | yes (sandbox)    |
| `prod`      | false           | interactive     | false         | **no**        | yes              |

**Key invariant:** `chaos_allowed=false` ONLY in `prod`. Every other profile can be chaos-tested.

**Storage namespace** differs per profile so concurrent runs don't collide:

- `backtest/<run_id>/` — owned by one backtest run; isolated writes.
- `paper/<client_id>/` — per-client paper trading namespace.
- `mock/<run_id>/` — local dev.
- `staging/`, `prod/` — shared live namespaces.

**Consumption:** deployment-api accepts `runtime_profile` on `POST /deployments` and fans out to the five env vars at
VM/pod boot. The UI shows one dropdown.

## 5. Chaos injection contract

Eight injection points are exposed. Each is a named boundary in the code with a registered hook location:

| Point               | Boundary                   | Hook location                                  |
| ------------------- | -------------------------- | ---------------------------------------------- |
| `venue_latency`     | execution venue adapter    | execution_service.adapters.venue_adapter_base  |
| `rpc_timeout`       | UCI cloud SDK wrappers     | unified_cloud_interface.clients                |
| `recon_mismatch`    | PBM reconciler             | position_balance_monitor_service.recon         |
| `price_shock`       | MTDS live feed             | market_tick_data_service.market_interface.feed |
| `instrument_delist` | instruments publisher      | instruments_service.publisher                  |
| `config_flip`       | UCI config reloaders       | unified_trading_library.config_reloader        |
| `kill_switch_fire`  | UTL KillSwitchBus          | unified_trading_library.kill_switch            |
| `component_failure` | ServiceBootstrap lifecycle | unified_trading_library.service_runtime        |

The UTL `ChaosController` reads active `ChaosInjectionSpec` records and applies them at these boundaries. It is a no-op
when `runtime_profile.chaos_allowed=false` (i.e., in prod).

Kill-switch semantics for `kill_switch_fire`:

- Scopes: GLOBAL, CLIENT, VENUE, STRATEGY, ARCHETYPE, INSTRUMENT.
- Default live behaviour on fire: delta-neutral exit (cheapest).
- Recon must be healthy before a close is permitted; dual failure (recon + exec both down) escalates to human-required.

## 6. Archetype → topology requirements (strategy v2)

Every archetype doc in `codex/09-strategy/architecture-v2/archetypes/` carries a `topology_requirements` block declaring
its demands. Strategy-service refuses to start if the materialised deployment does not satisfy them (runtime reader:
`strategy_service/topology_enforcement.py::load_topology_requirements()`).

The table is the per-archetype projection of the binding decision artifact
(`/codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md` § "2026-08-10 — FINAL DECISION ARTIFACT") and the machine
mapping `unified_api_contracts.ARCHETYPE_TO_DEPLOYMENT_PROFILE`. Derivation rule: every `Low`→`co_located_vm` archetype
requires `strategy: isolated` + `co-location: yes` + `min SLA: premium`; every `Medium`/`High`→`distributed` archetype
requires `strategy: shared OK` + `co-location: no` + `min SLA: standard`. (Execution is always isolated. Strategy
isolation is the differentiator.)

| Archetype                             | execution | strategy  | co-location                    | min SLA  |
| ------------------------------------- | --------- | --------- | ------------------------------ | -------- |
| `ML_DIRECTIONAL_CONTINUOUS`           | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `ML_DIRECTIONAL_EVENT_SETTLED`        | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `RULES_DIRECTIONAL_CONTINUOUS`        | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `RULES_DIRECTIONAL_EVENT_SETTLED`     | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `TSMOM_BTC_CTA`                       | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `CARRY_BASIS_DATED`                   | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `CARRY_BASIS_DATED_INV`               | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `CARRY_BASIS_PERP`                    | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `CARRY_BASIS_PERP_INV`                | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `CARRY_FUNDING_DISPERSION`            | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `CARRY_STAKED_BASIS`                  | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `CARRY_STAKED_BASIS_DATED`            | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `CARRY_RECURSIVE_STAKED`              | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `CARRY_RECURSIVE_BORROW_LENDING_ONLY` | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `YIELD_ROTATION_LENDING`              | isolated  | shared OK | no                             | standard |
| `YIELD_STAKING_SIMPLE`                | isolated  | shared OK | no                             | standard |
| `ARBITRAGE_PRICE_DISPERSION`          | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `ARBITRAGE_SPORTS_DUTCHING`           | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `LIQUIDATION_CAPTURE`                 | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `ARBITRAGE_MEV_SANDWICH`              | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `ARBITRAGE_MEV_JIT_LIQUIDITY`         | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `ARBITRAGE_MEV_BACKRUN`               | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `ARBITRAGE_MEV_LIQUIDATION_BUNDLE`    | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `ARBITRAGE_CROSS_DOMAIN_EVENT`        | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `MARKET_MAKING_CONTINUOUS`            | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `MARKET_MAKING_EVENT_SETTLED`         | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `MARKET_MAKING_PASSIVE_SPREAD`        | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `MARKET_MAKING_INVENTORY_SKEW`        | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `MARKET_MAKING_ML_LEAN`               | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `MARKET_MAKING_QUEUE_MICROSTRUCTURE`  | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `MARKET_MAKING_PREDICTION`            | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `DEFI_LP_CONCENTRATED`                | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `DEFI_LP_POOL`                        | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `DEFI_LP_VAULT`                       | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `EVENT_DRIVEN`                        | isolated  | shared OK | no                             | standard |
| `VOL_TRADING_OPTIONS`                 | isolated  | shared OK | no                             | standard |
| `VOL_ARB_RV_IV`                       | isolated  | shared OK | no                             | standard |
| `VOL_SPREAD_STRUCTURES`               | isolated  | shared OK | no                             | standard |
| `VOL_CARRY`                           | isolated  | shared OK | no                             | standard |
| `VOL_OVERLAY_COVERED_CALLS`           | isolated  | shared OK | no                             | standard |
| `VOL_OVERLAY_PROTECTIVE_PUT`          | isolated  | shared OK | no                             | standard |
| `VOL_STRADDLE`                        | isolated  | shared OK | no                             | standard |
| `VOL_SYNTHETIC_DELTA`                 | isolated  | shared OK | no                             | standard |
| `VOL_MARKET_MAKING`                   | isolated  | shared OK | no                             | standard |
| `VOL_ML_LEAN`                         | isolated  | shared OK | no                             | standard |
| `VOL_0DTE_GAMMA_SCALPING`             | isolated  | shared OK | no                             | standard |
| `VOL_0DTE_PIN_RISK`                   | isolated  | shared OK | no                             | standard |
| `VOL_TERM_STRUCTURE_ARB`              | isolated  | shared OK | no                             | standard |
| `VOL_TERM_STRUCTURE_SLOPE`            | isolated  | shared OK | no                             | standard |
| `VOL_DISPERSION`                      | isolated  | shared OK | no                             | standard |
| `VOL_VARIANCE_SWAP`                   | isolated  | shared OK | no                             | standard |
| `VOL_LEAPS_CONVEXITY`                 | isolated  | shared OK | no                             | standard |
| `VOL_CROSS_ASSET_SPREAD`              | isolated  | shared OK | no                             | standard |
| `VOL_RATIO_SPREAD`                    | isolated  | shared OK | no                             | standard |
| `STAT_ARB_PAIRS_FIXED`                | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `STAT_ARB_CROSS_SECTIONAL`            | isolated  | isolated  | yes (exec+strategy on same VM) | premium  |
| `PORTFOLIO_MULTI_STRATEGY`            | isolated  | shared OK | no                             | standard |
| `PORTFOLIO_RISK_PARITY`               | isolated  | shared OK | no                             | standard |
| `PORTFOLIO_FACTOR_ALLOCATION`         | isolated  | shared OK | no                             | standard |
| `PORTFOLIO_TACTICAL_OVERLAY`          | isolated  | shared OK | no                             | standard |

## 7. Worked examples

### Example A — small client on premium

- Client: `client_alpha`
- Subscription: `sla_tier=premium`, no overrides.
- Resolved topology:
  - instruments, market-tick-data, MDPS, features, ML → shared pool.
  - strategy-service → **isolated** (premium mandates).
  - execution-service → **isolated** (always).
  - PBM, risk, pnl → **isolated** (premium mandates).
  - alerting → shared (not in premium's min_isolated).
- Cost: 6.0× base for 4 isolated services + shared-pool share.

### Example B — mid-tier client on standard, upgraded risk

- Client: `client_beta`
- Subscription: `sla_tier=standard`, override `{risk-and-exposure-service: isolated}`.
- Resolved topology:
  - All shared services → shared pool.
  - strategy-service → shared (standard doesn't mandate isolated).
  - execution-service → isolated (standard mandates).
  - risk-and-exposure-service → isolated (override, allowed).
  - PBM, pnl, alerting → shared.
- Cost: 2.5× base + line-item delta for isolated risk.

### Example C — multi-tenant pool (basic clients)

- Clients: `client_gamma`, `client_delta`, `client_epsilon` all on `basic`.
- Resolved topology:
  - All services shared EXCEPT execution-service (one instance per client — always).
  - One shared pool per service, clients multiplexed by `client_id` on the topic.
- Cost: 1.0× base per client, shared infra amortised.

## 8. What does NOT change

- Transport protocol resolution (UTL `get_messaging_protocol`, `get_storage_protocol`, `resolve_transport`) is
  unchanged.
- Cluster YAMLs for deployment-service remain the SSOT for cluster composition.
- `workspace-manifest.json` is unchanged.
- The 67-repo architecture is unchanged.
- UAC facade pattern is unchanged.

## 9. Follow-ups (tracked in deployment_topology_and_client_isolation_2026_04_17.plan.md)

- Phase 2: deployment-service + deployment-api materialisation.
- Phase 3: UTL `ChaosController` + `KillSwitchBus`.
- Phase 4: runtime_profile UI axis.
- Phase 5: archetype `topology_requirements` frontmatter per family doc.
- Phase 6: PBM/risk/pnl/execution client_id routing enforcement.
- Phase 7: e2e-testing chaos scenarios.
- Phase 8: workspace-wide QG sweep.

## 10. See also

- `unified-trading-pm/configs/runtime-topology.yaml` — machine SSOT.
- `unified-trading-pm/codex/04-architecture/runtime-deployment-topology.md` — paired decisions doc.
- `unified-trading-pm/codex/05-infrastructure/runtime-tiers-and-deployment.md` — runtime tier (T0-T6) definitions.
- `unified-trading-pm/codex/09-strategy/architecture-v2/README.md` — strategy family/archetype catalog.
- `unified-api-contracts/unified_api_contracts/internal/domain/deployment_service/isolation.py` — Pydantic schemas.
- `unified-trading-library/unified_trading_library/topology/topology_reader.py` — runtime readers.
