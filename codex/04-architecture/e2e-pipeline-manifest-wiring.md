---
scope: [engineer, admin]
last_reviewed: 2026-06-02
---

# E2E Pipeline Manifest Wiring — IS → MTDS → MDPS → features → strategy → execution

> **Codified**: 2026-06-02 (slot 7, operator request: "UAC/IS/MTDS/MDPS/features/strategy/execution all hooked up for
> E2E + data manifest + data status; deployment UI/API need to understand and show them"). Scope of this doc =
> **verify + document** the current wiring and name the gaps. SSOT for the live state is the code referenced inline;
> this doc is the map. Companion:
> [`../02-data/availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md).
> Machine-checked by `system-integration-tests/tests/unit/test_pipeline_manifest_wiring.py`.

## The chain

```
instruments-service ──instruments──▶ MTDS ──raw_tick_data──▶ MDPS ──processed_candles──▶ features-service ──*_features──▶ strategy-service ──strategy_orders──▶ execution-service
        (IS)                       (raw market data)        (OHLC candles)            (delta_one/onchain/vol/…)        (signals/orders)        (fills/positions)
```

UAC is **schema-only** — it defines the contracts every stage speaks (`CaptureStatus`, the 33-member
`EmptyConfirmedReason` closed set, `pipeline_mode`, `source`, the `AvailabilityRecord` row) and emits no manifest rows
of its own. That is correct, not a gap.

## Three layers, verified independently

### Layer 1 — manifest emission (per-service writer wiring) ✅ COMPLETE

Every producing service writes availability-manifest rows via the UTL `ManifestWriter`
(`unified_trading_library/manifest_writer.py`) with its own `service_name`:

| Stage      | Service                        | `service_name`                   | Emits via                                                                                 |
| ---------- | ------------------------------ | -------------------------------- | ----------------------------------------------------------------------------------------- |
| 0 (schema) | unified-api-contracts          | — (none)                         | schema-only; defines `AvailabilityRecord`, `CaptureStatus`, `EmptyConfirmedReason`        |
| 1          | instruments-service            | `instruments-service`            | `record_captured`/`record_empty` (43 source files reference the writer)                   |
| 2          | market-tick-data-service       | `market-tick-data-service`       | writer + `record_failed` for uptime gaps / partition bias / malformed fields (101 files)  |
| 3          | market-data-processing-service | `market-data-processing-service` | `candle_write_mixin` / `orchestration_service` (35 files)                                 |
| 4          | features-service               | `features-service`               | per feature_group + `feature_family` sibling-presence guard (38 files)                    |
| 5          | strategy-service               | `strategy-service`               | per `strategy_id` (`save_operations` / `cloud_strategy_storage`) (8 files)                |
| 6          | execution-service              | `execution-service`              | `results/save_operations.py:737` `record_captured`, keyed by `instruction_type` (5 files) |

**Schema can represent every hop.** `AvailabilityRecord` (v9, `MANIFEST_SCHEMA_VERSION = 9`) carries the stage-key
columns for the whole chain: `service_name`, `data_type`, `instrument_type`, `feature_group`, `feature_family`,
`strategy_id`, `client_id`, `instruction_type`, plus `job_id`, `pipeline_mode`, `source`. No schema gap blocks E2E
representation.

### Layer 2 — readiness dependency graph (cross-service preflight) ⚠️ ONE MISSING HOP

`unified_trading_library/dependency_check.py` `PIPELINE_DEPENDENCIES` is the SSOT for "what each service reads
upstream"; `check_upstream_ready()` consumes it to gate processing. Current edges:

| Consumer                       | Upstream dataset                          | Upstream service               | required |
| ------------------------------ | ----------------------------------------- | ------------------------------ | -------- |
| market-tick-data-service       | `instruments`                             | instruments-service            | yes      |
| market-data-processing-service | `raw_tick_data`                           | market-tick-data-service       | yes      |
| features-onchain-service       | `raw_tick_data`                           | market-tick-data-service       | no       |
| features-delta-one-service     | `processed_candles`                       | market-data-processing-service | yes      |
| features-volatility-service    | `processed_candles`                       | market-data-processing-service | yes      |
| strategy-service               | `onchain_features` / `delta_one_features` | features-\*-service            | yes / no |

**GAP G-EXEC — execution-service has no `PIPELINE_DEPENDENCIES` entry.** It is the only pipeline producer with no
declared upstream, even though (a) it emits its own manifest rows, and (b) the natural upstream dataset already exists
in `PATH_REGISTRY`: `strategy_orders` (and `strategy_instructions`). So the readiness chain is wired
`IS→MTDS→MDPS→features→strategy` but **stops at strategy** — there is no machine-checkable "strategy output is ready
before execution consumes it" edge. Whether execution _should_ gate on a `strategy_orders` manifest (batch) vs. consume
strategy signals over the event bus (live) is the open design question; adding the edge is additive and low-risk (the
dict entry only takes effect where a caller invokes `check_upstream_ready`). Tracked as a follow-up todo — do not
silently mutate this core SSOT without confirming strategy actually writes a `strategy_orders` manifest.

### Layer 3 — data-status surface (deployment-api / deployment-ui) ⚠️ PER-SERVICE ONLY + UI DRIFT

- **deployment-api** (`deployment_api/services/data_status_service.py` + `routes/data_status.py`) exposes a rich
  `/api/data-status/*` surface (manifest, turbo, drilldown, coverage-summary, shard-detail, leaf-stats, venue-detail)
  reading each service's bucket via UTL `read_availability_index`. Per-service coverage for all stages is essentially
  complete (`SERVICE_TO_KIND` maps IS, MTDS, MDPS, features-\* families, strategy-service→`strategy-store`,
  execution-service→`execution-store`).
- **GAP G-TRACE — no cross-service E2E trace.** There is no `pipeline-trace?instrument&date` endpoint that threads one
  instrument/venue/date through all stages and reports `capture_status` per hop. Today the operator reads 7 isolated
  per-service panels and threads dependencies mentally. (Out of scope for the verify+document pass; named here as the
  primary future feature.)
- **GAP G-UI — deployment-ui service-list drift.** `deployment-ui/src/components/DataStatusTab.tsx`
  `DATA_PIPELINE_SERVICES` hardcodes `features-cefi-service`/`features-defi-service`/`features-tradfi-service`/
  `features-prediction-service` and **omits strategy-service**, while the backend `SERVICE_TO_KIND` uses the real
  consolidated families (`features-delta-one-service`, `features-volatility-service`, `features-onchain-service`,
  `features-sports-service`, …). The UI list does not match what the API serves; execution lives in a separate
  `ExecutionDataStatus` component disconnected from the pipeline view. Should be UAC/discovery-driven, not hardcoded.
  (UI change → gated by the playwright HARD RULE; tracked as a follow-up todo, not changed here.)

## Known smaller findings

- **`service_name` plural drift:** execution-service writes `service_name="execution-service"` in
  `results/save_operations.py` but `"execution-services"` (plural) in `cli/backtest.py:127-129`. Two distinct
  `service_name` strings for one producer fragments its manifest identity; reconcile to the singular canonical form.

## Coordination

Active in-flight work on the data-status canonicalisation/migration surface lives in
`plans/active/downstream_services_manifest_canonicalisation_2026_06_01.md` (deployment-api/UI preflight, "agent B", +
slot-2 DeFi sub-bucket scope). The gaps named here (G-EXEC, G-TRACE, G-UI) are **additive** and must not collide with
that migration scope.

## What is machine-checked

`system-integration-tests/tests/unit/test_pipeline_manifest_wiring.py` asserts: (1) every `PIPELINE_DEPENDENCIES`
upstream `dataset` resolves to a real `PATH_REGISTRY` key (no runtime `KeyError`); (2) every upstream `service_name` is
a recognized producer; (3) the readiness chain is transitively reachable from `instruments-service` through
`strategy-service`; (4) `AvailabilityRecord` carries every stage-key column; (5) **G-EXEC** — the strategy→execution
edge — as an `xfail` that names this doc, so it passes today but flips to `xpass` (prompting removal) the moment the
edge is wired.
