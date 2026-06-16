---
scope: [engineer]
created: 2026-05-12
ssot_plan: plans/active/client_reporting_pnl_attribution_mvp_2026_05_10.md Phase 7.A
last_reviewed: 2026-05-17
---

# Client Reporting Architecture

> **Single-entry SSOT** for the per-client NAV / PnL / attribution pipeline. The underlying factor × layer model lives
> in [`pnl-attribution.md`](../09-strategy/architecture-v2/cross-cutting/pnl-attribution.md) — do NOT duplicate the
> factor closed set or invariant definitions here; reference them.

## Lineage flow

```
position-balance-monitor-service       execution-service
  (PositionEvent w/ archetype_id         (FillAttributionContext w/
   strategy_leg_id, trade_id)             client_id, trade lineage)
           |                                      |
           +------------------+-------------------+
                              |
                   UTL pnl_attribution.joiner
                   (join on client_id / archetype_id / trade_id / ts_window)
                              |
                   UTL pnl_attribution.emitter
                              |
                 GCS: {client-reports bucket}/{client_id}/{archetype}/{YYYY-MM-DD}/attribution.parquet
                              |
                   client-reporting-api
                   (/api/v1/clients/{client_id}/nav|pnl|positions|attribution)
                              |
                   deployment-ui
                   (ClientReportingTab — NavChart, PnLChart, AttributionChart, DrilldownTable)
```

## Attribution parquet shape

Every file at `{client-reports bucket}/{client_id}/{archetype}/{YYYY-MM-DD}/attribution.parquet` contains rows of
`PnLAttributionRow` (UAC `unified_api_contracts.internal.risk`):

| Field             | Type            | Notes                                                                         |
| ----------------- | --------------- | ----------------------------------------------------------------------------- |
| `strategy_id`     | `str`           | Fully-qualified `FAMILY.ARCHETYPE.slot_id`                                    |
| `instrument_id`   | `str`           | UAC canonical instrument id                                                   |
| `archetype_id`    | `str`           | e.g. `carry_staked_basis`                                                     |
| `factor`          | `PnLFactor`     | Closed 16-factor set — see pnl-attribution.md § Canonical Attribution Factors |
| `layer`           | `PnLLayer`      | `STRATEGY` or `EXECUTION` — see pnl-attribution.md § 7                        |
| `amount`          | `Decimal`       | Signed USD contribution                                                       |
| `fill_id`         | `str\|None`     | Trace back to the execution fill                                              |
| `venue`           | `str\|None`     | Venue where fill occurred                                                     |
| `benchmark_price` | `Decimal\|None` | BENCHMARK fill price for execution-alpha delta                                |
| `timestamp`       | `datetime`      | UTC write time                                                                |

Bucket resolver:
`unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(cloud=..., kind="client-reports", ...)`. Kind
`client-reports` is defined in `deployment-service/configs/cloud-providers.yaml`.

## Decomposition invariants

Enforced by `unified_trading_library.pnl_attribution.invariants.assert_decomposition_invariants()` per (client,
archetype, day):

1. `sum(rows, all factors, both layers) == realised_total_pnl == ClientNAV.delta`
2. `sum(rows where layer=STRATEGY) == strategy_alpha_total`
3. `sum(rows where layer=EXECUTION) == execution_alpha_total`
4. `RESIDUAL factor magnitude < 1% of |total_pnl|`
5. Every row `factor ∈ PnLFactor` and `layer ∈ PnLLayer`

Violation raises `DecompositionInvariantError` (UTL). Never silently swallow — per honest-absence rule.

## Attribution rollup view

The API layer (`attribution_reader.py`) reads parquets and exposes three rollup views:

| Endpoint                               | Aggregation                                                    |
| -------------------------------------- | -------------------------------------------------------------- |
| `GET /api/v1/clients/{id}/nav`         | Sum all rows per date → NAV delta snapshot                     |
| `GET /api/v1/clients/{id}/pnl`         | Sum by layer per date → strategy_alpha / execution_alpha split |
| `GET /api/v1/clients/{id}/attribution` | Raw rows grouped by (strategy_id, instrument, factor, layer)   |
| `GET /api/v1/clients/{id}/positions`   | Live snapshot from position-balance-monitor parquet (Phase 8+) |

Mock mode (`CLOUD_MOCK_MODE=true`): all endpoints return stub data with `client_id` echoed from path — no parquet reads.

## Client seed

The May-23 demo client is seeded from UAC `unified_api_contracts.registry.client_share_classes`:

| Field         | Value                                         |
| ------------- | --------------------------------------------- |
| `client_id`   | `DEMO_CLIENT_ID = "demo-internal"`            |
| `share_class` | `ShareClass.USDT`                             |
| `mode`        | `ClientReportingMode.DEMO`                    |
| `archetypes`  | `carry_staked_basis`, `leveraged_funding_arb` |

## Cross-references

- Factor × layer dual axis (Hard Rule #7 + PnLFactor closed set + Decomposition Invariants):
  [pnl-attribution.md](../09-strategy/architecture-v2/cross-cutting/pnl-attribution.md)
- Batch = live (benchmark-fills contract that isolates strategy_alpha from execution_alpha):
  [batch-live-architecture.md § 5-6](batch-live-architecture.md)
- Backtest groups (Group C execution fills feed the attribution joiner): [backtest-groups.md](backtest-groups.md)
- Bucket naming SSOT: `deployment-service/configs/cloud-providers.yaml` kind `client-reports`
- Emitter implementation: `unified_trading_library.pnl_attribution.emitter`
- API routes: `client-reporting-api/client_reporting_api/api/routes/attribution.py`
- UI tab: `deployment-ui/src/components/ClientReportingTab.tsx`
- Plan (full Phase list + done/todo): `plans/active/client_reporting_pnl_attribution_mvp_2026_05_10.md`
