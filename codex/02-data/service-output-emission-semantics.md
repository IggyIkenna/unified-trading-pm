---
scope: [engineer]
status: active
last_updated: 2026-05-11
owner: ikenna
related_plans:
  - plans/active/writegate_honest_coverage_endtoend_2026_05_06.md
  - plans/active/manifest_schema_final_gate_2026_05_09.md
related_codex:
  - codex/02-data/availability-manifest-and-data-status.md
  - codex/02-data/honest-absence-downstream-handling.md
last_reviewed: 2026-05-17
---

# Service-output emission semantics

> **STATUS** (2026-05-11): slice (a) shipped UAC@`58c3b61` + UTL@`1a7e1d4b` (4-state policy enum + lifecycle events +
> `publish_with_policy()`); slice (b) shipped UTL@`ac5ade59` + MDPS@`9e1a93e` (manifest_completeness helper +
> publish_with_manifest_lookup wrapper + ohlcv_1h POC); slice (c) Phase 6.1-6.9 covers the remaining 8 services
> (multi-week rollout). v8 manifest schema columns for `service_emission_state` + `last_emission_decision_at` +
> `expected_window_completeness_fraction` are owned by
> [`manifest_schema_final_gate_2026_05_09.md`](../../plans/active/manifest_schema_final_gate_2026_05_09.md) Phase 1 —
> **shipped 2026-05-11 at UAC@`174f401`** + rename @ UAC@`76f950a`
> (`unified_api_contracts.canonical.crosscutting.manifest_schema` declares `MANIFEST_SCHEMA_VERSION_V8 = 8` +
> `V8_NEW_COLUMNS` + `V8_COLUMN_DEFAULTS` + `READER_FALLBACK_WINDOW_DAYS`;
> `unified_api_contracts.canonical.crosscutting.service_emission_state` declares `ServiceEmissionStateEnum` +
> `SERVICE_EMISSION_STATES` frozenset + `ManifestRowBlockedError`;
> `service_emission_policy.next_state(*, policy, event)` resolves `(ServiceEmissionPolicy, EmissionLifecycleEvent)` →
> `ServiceEmissionStateEnum` for the writer hot path). The third column was originally shipped as
> `expected_window_completeness_pct` at UAC@`174f401`; renamed to `_fraction` at UAC@`76f950a` per
> [`plans/active/issues/expected_window_completeness_pct_range_drift_2026_05_11.md`](../../plans/archive/issues/expected_window_completeness_pct_range_drift_2026_05_11.md)
> option (a) — value range is 0-1 fraction, not 0-100 percentage; aligns with UTL `completeness_fraction` arg.

## TL;DR

Every service that emits a derived / aggregated output (MDPS hourly candles, features-\* feature_groups, ml-\* model
versions, strategy archetype signals, execution order_intent/fill confirmations, position-balance portfolio_state,
risk-and-exposure risk_state, instruments-service catalog snapshots) MUST route its publish boundary through
`unified_trading_library.emission_publisher.publish_with_policy()` (or `publish_with_manifest_lookup()` when the
upstream completeness is computed from manifest reads).

The publisher resolves a 4-state policy from the SSOT in
`unified_api_contracts.canonical.crosscutting.service_emission_policy.SERVICE_OUTPUT_POLICIES` (keyed by
`(service, output_data_type)`), evaluates the caller-supplied `completeness_fraction`, decides whether to publish the
row + whether to fire an alert, and emits the matching lifecycle event.

## The 3 stacked layers

```
                            ┌──────────────────────────────────────────────┐
Layer 3 — Service emission  │ publish_with_policy(...)                    │
(this doc)                  │   → EmissionDecision(policy, event,         │
                            │     should_publish_row, should_alert,       │
                            │     completeness_fraction, ...)             │
                            │                                              │
                            │ Owners: every derived/aggregated service    │
                            │ Policy SSOT: UAC SERVICE_OUTPUT_POLICIES    │
                            └──────────────────┬───────────────────────────┘
                                               │
                            ┌──────────────────▼───────────────────────────┐
Layer 2 — Service output    │ Service writes parquet rows + manifest      │
completeness                │ row. Completeness fraction derived from     │
                            │ upstream manifest 4-state at write-time.    │
                            │                                              │
                            │ Helper: manifest_completeness.compute_       │
                            │ completeness_fraction(upstream_window, ...) │
                            └──────────────────┬───────────────────────────┘
                                               │
                            ┌──────────────────▼───────────────────────────┐
Layer 1 — Manifest 4-state  │ ManifestWriter writes one of:               │
                            │   captured / empty_confirmed /              │
                            │   attempted_failed / expected_unattempted   │
                            │                                              │
                            │ SSOT: CLAUDE.md "Availability manifest v5". │
                            └──────────────────────────────────────────────┘
```

## The 4 policies

Closed set in `unified_api_contracts.canonical.crosscutting.service_emission_policy.ServiceEmissionPolicy`:

| Policy           | When upstream has gaps (`completeness_fraction < 1.0`)                                                                                              | Use case                                                                                                             |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `STRICT_FAIL`    | Suppress the row. Emit `STALE_DATA` heartbeat-only event. Downstream sees: service UP (still emitting), data STALE (no metric row).                 | Real-time current-bar emissions (`ohlcv_1m:current`, `ohlcv_1h:current`, paired_spec for cross-instrument features). |
| `PARTIAL_OK`     | Publish the row + emit `PUBLISHED_DEGRADED` event with the `completeness_fraction`. Downstream consumer branches on the fraction per its tolerance. | Historical re-emissions (`ohlcv_1h:historical`), aggregate metrics (`high_low_24h`).                                 |
| `NAN_FILL`       | Publish the row + emit `PUBLISHED_DEGRADED` event. The row contains NaN for the gap-contributing columns; tree-based ML tolerates per NaN-policy.   | Rolling-window features (`vol_30d`, `pairwise_correlation`).                                                         |
| `BLOCK_CRITICAL` | Suppress the row + fire a P0 alert via alerting-service. Emit `BLOCKED` event. Operator triages.                                                    | Position state during venue-down; ml-training model_version publish; execution `fill_confirmation` (position-truth). |

`completeness_fraction == 1.0` always emits `PUBLISHED_OK` + publishes the row regardless of policy — no gap = no
decision.

## The 4 lifecycle events

Closed set in `EmissionLifecycleEvent`:

- `PUBLISHED_OK` — full window, row written, INFO severity.
- `PUBLISHED_DEGRADED` — gap + permissive policy, row written, WARNING severity.
- `STALE_DATA` — gap + `STRICT_FAIL`, no row, WARNING severity (heartbeat).
- `BLOCKED` — gap + `BLOCK_CRITICAL`, no row, ERROR severity + alert flag.

Every event carries `completeness_fraction`, `incomplete_window_count`, `policy`, and `row_key` in the metadata payload.
A 50-row sample of `incomplete_window` is inlined for operator drill-down.

## Slice differentiation (`:current` vs `:historical`)

`output_data_type` carries an optional `:<slice>` suffix when real-time and historical re-emission warrant different
policies for the same underlying type. The MDPS ohlcv_1h POC (slice (b)) is the canonical example:

| `output_data_type`    | Slice resolver                                                                | Typical policy | Behaviour on gap                                                  |
| --------------------- | ----------------------------------------------------------------------------- | -------------- | ----------------------------------------------------------------- |
| `ohlcv_1h:current`    | `_resolve_emission_slice(date_str) == "current"` when `date_str` == today UTC | `STRICT_FAIL`  | Suppress row (live consumer needs full current bar or no bar)     |
| `ohlcv_1h:historical` | `date_str < today UTC`                                                        | `PARTIAL_OK`   | Publish row with `fraction < 1.0` (historical backfill tolerates) |

Per CLAUDE.md "Live = batch — same code path" rule, there is NO separate live vs batch writer. The same
`canonical_writer.write_candle_parquet` serves both; only the resolved `output_data_type` tag differs. Adapters MUST NOT
branch on a `mode=live` / `mode=batch` flag at the writer level.

## Helper API surface

All in `unified_trading_library.emission_publisher` + `unified_trading_library.manifest_completeness`:

### `publish_with_policy(*, service, output_data_type, row_key, completeness_fraction, incomplete_window=None, correlation_id=None, extra_event_details=None) -> EmissionDecision`

Pure publish-boundary helper — no manifest read, no I/O beyond the lifecycle event emit. Caller computes the
completeness fraction however it wants (manifest-grain via `manifest_completeness`, bar-level via parquet inspection,
synthetic for backtests). Returns `EmissionDecision` carrying the `should_publish_row` flag the caller branches on.

### `publish_with_manifest_lookup(*, service, output_data_type, row_key, bucket, upstream_window, manifest_index=None, force_refresh=False, ...) -> EmissionDecision`

Convenience wrapper combining `compute_completeness_fraction()` + `publish_with_policy()` in one call. Reads the
canonical availability index via `read_availability_index(bucket)` (60s TTL cache); `force_refresh=True` invalidates;
`manifest_index=<pd.DataFrame>` short-circuits the read for callers with the index already.

### `compute_completeness_fraction(*, bucket, upstream_window, manifest_index=None, force_refresh=False) -> CompletenessReadout`

Standalone helper for callers that want to compute the fraction without publishing (e.g. diagnostics, data-status
endpoints, audit reports). Returns frozen `CompletenessReadout` with the fraction + the `incomplete_window` list +
per-state totals.

### `next_state(*, policy: ServiceEmissionPolicy, event: EmissionLifecycleEvent) -> ServiceEmissionStateEnum`

Pure resolver (`unified_api_contracts.canonical.crosscutting.service_emission_policy`) that maps the lifecycle event the
publisher just emitted to the v8 manifest column value. Three of four events map 1:1; `STALE_DATA` renames to
`STALE_DATA_HEARTBEAT_ONLY` so the manifest column self-documents the "heartbeat-only, no metric row" semantic. The
`policy` arg is advisory (state derives from `event` under the slice (b) spec; kept in signature for forward-compat with
future policy-specific state nuances). UTL's writer hot path calls this after `publish_with_policy(...)` to fill the
`service_emission_state` v8 column. Shipped at UAC@`174f401` per `manifest_schema_final_gate_2026_05_09.md` Phase 1.B.

## Manifest-read protocol per `service_emission_state`

Downstream consumers reading the v8 manifest column MUST branch on the four states:

| State                       | Consumer action                                                                                                                                                                                                                                                                          |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PUBLISHED_OK`              | Consume normally — full upstream window represented.                                                                                                                                                                                                                                     |
| `PUBLISHED_DEGRADED`        | Consume with the row's `completeness_fraction` column applied per the per-service consumer-class audit (NaN-fill / rolling-window denominator adjust / propagate-per-leg).                                                                                                               |
| `STALE_DATA_HEARTBEAT_ONLY` | **Skip + log.** No metric row was written; service is up + emitting heartbeat events. Downstream MUST NOT proxy-fill from prior windows — the absence is the signal.                                                                                                                     |
| `BLOCKED`                   | **Skip + raise `ManifestRowBlockedError`** (`unified_api_contracts.canonical.crosscutting.service_emission_state`). The publish-boundary policy withheld the metric row + fired a P0 alert; any downstream read is a correctness-critical attempt to consume data deliberately withheld. |
| `None` (legacy v7 row)      | Fall through to `capture_status`-based reasoning. The ≤30-day reader-fallback window (`READER_FALLBACK_WINDOW_DAYS = 30`) expires ~2026-06-14 per Phase 7 walk.                                                                                                                          |

> **Reader-fallback retirement gate** (per codex audit D-4 2026-05-12): the `READER_FALLBACK_WINDOW_DAYS = 30` fallback
> chain is deleted at the Phase 7 walk owned by
> [`plans/active/manifest_schema_final_gate_2026_05_09.md`](../../plans/active/manifest_schema_final_gate_2026_05_09.md)
> Phase 7. Operator gating: deletion is permitted only when the `READER_FELL_BACK_TO_LEGACY_PATH` event-count threshold
> reaches **zero across the workspace for 7 consecutive days** (per
> [`pipeline-mode-partition.md`](./pipeline-mode-partition.md) § "Reader fallback chain"). The QG step enforcing
> deletion is `unified-trading-pm/scripts/quality_gates/check_reader_fallback_retired.py` (lands with Phase 7).
> Cross-references: [`pipeline-mode-partition.md`](./pipeline-mode-partition.md) § Reader fallback chain (line 104+).

## When the policy gate is n/a — MTDS raw capture

Not every service is a derived-output emitter. **MTDS is n/a per the slice (c) Phase 6.1 audit** (2026-05-12, harsh slot
3). MTDS is the ORIGINATOR of every data*type it produces: ticks / candles / book snapshots / DeFi reserve params all
come from external APIs (Databento / Tardis / Hyperliquid REST / Pyth Hermes / chain RPCs / sportstats vendors). There
is no \_upstream MTDS service* whose completeness gates the write — the upstream is the venue / vendor, and the manifest
layer (`record_captured` / `record_empty(reason=)` / `record_failed`) is sufficient.

Workspace audit (2026-05-12): `rg "publish_with_policy|publish_with_manifest_lookup" market_tick_data_service/` returns
**zero** callsites. MTDS adapters universally call `ManifestWriter.record_captured` for raw captures. Adapters that _do_
transform source responses — `umi_tick_provider._fetch_databento_ohlcv_1m_async` (Databento direct 1m candle feed),
`gas_price_adapter._aggregate` (block-level fee rollup to hourly/daily), Hyperliquid `_aggregate` (orderbook depth
bucketing) — are SOURCE-side transformations, not aggregations of MTDS-written upstream rows. They stay on the
raw-capture path.

**Drift watch**: if a future MTDS handler reads from a _prior MTDS write_ to compute a derived row (cross-handler
aggregation), that's the trigger to wire `publish_with_policy` + register a `(market-tick-data-service, <output_dt>)`
seed entry in `SERVICE_OUTPUT_POLICIES`. Today (post Phase 6.1 audit), no such handler exists.

Same logic applies to `instruments-service` reference-data adapters that fetch directly from venue catalogs
(api_football / footystats / Polymarket gamma_api / Databento product reference). Those route through the manifest
layer's per-row `record_captured` without a service-output policy gate — the catalog_snapshot policy entry
(`PARTIAL_OK`) only fires at a future "consolidated daily catalog snapshot" emission boundary which today is computed at
read-time via `read_availability_index(bucket)`. Per writegate Phase 6.8 sub-plan ownership.

## Worked examples

### MDPS `ohlcv_1h:current` — STRICT_FAIL on gap

Service: `market-data-processing-service`. Upstream: 60 × `ohlcv_1m` shards (manifest-grain: 1 ohlcv_1m row per day per
shard). Live emission at hour H of day D for `(BINANCE, BTC-USDT, spot)`:

```python
decision = publish_with_manifest_lookup(
    service="market-data-processing-service",
    output_data_type="ohlcv_1h:current",
    row_key={"date": "2026-05-08", "venue": "BINANCE", "data_type": "ohlcv_1h", ...},
    bucket="market-data-tick-cefi-prod-...",
    upstream_window=[{"date": "2026-05-08", "venue": "BINANCE", "data_type": "ohlcv_1m", ...}],
)
if decision.should_publish_row:
    manifest_writer.record_captured(row_key=..., df=candles_df, ...)
# else: helper already emitted STALE_DATA heartbeat; no record_captured call.
```

Day D's ohlcv_1m manifest row in state `captured` → fraction=1.0 → `PUBLISHED_OK` + row written. State
`attempted_failed` → fraction=0.0 → `STALE_DATA` + no row.

### features-volatility `vol_30d` — NAN_FILL

Service: `features-volatility`. Upstream: 30 × daily `ohlcv_24h` manifest rows. NAN_FILL policy means the helper
publishes the row when 1-10% of the upstream window has gaps; the NaN-contributing columns carry NaN; tree-based ML
trains on the populated columns.

### execution-service `fill_confirmation` — BLOCK_CRITICAL

Service: `execution-service`. Upstream: per-venue real-time fill stream. BLOCK_CRITICAL policy means partial venue state
suppresses the fill_confirmation row AND fires a P0 alert — execution + position-balance cannot tolerate position-truth
violations.

## Anti-patterns

- **Don't call `ManifestWriter.record_captured` directly at a derived-service emission boundary without going through
  `publish_with_policy()`.** The QG STEP (writegate slice (c) Phase 6.9) statically walks every `record_captured(`
  callsite and asserts the paired publisher call when the data_type is a declared service-output.
- **Don't ship a service with `output_data_type` missing from `SERVICE_OUTPUT_POLICIES`.** Unseeded
  `(service, output_data_type)` pairs default to `STRICT_FAIL` per the UAC SSOT — forces explicit declaration.
- **Don't branch on `mode=live` / `mode=batch` at the publish boundary.** Per CLAUDE.md "Live = batch — same code path",
  the slice is resolved at write-time from `date_str` vs today's UTC date. Batch and live use the same helper.
- **Don't pass `completeness_fraction=0.0` defensively for missing upstream manifest reads.**
  `compute_completeness_fraction` distinguishes "missing-from-manifest" (treated as `expected_unattempted`) from
  manifest-read failure (raises). Defensive `0.0` masks the failure mode.
- **Don't emit lifecycle events outside the publisher.** Every `PUBLISHED_OK` / `PUBLISHED_DEGRADED` / `STALE_DATA` /
  `BLOCKED` event MUST come from `publish_with_policy()` so the metadata schema is uniform across services.

## Per-service rollout playbook (= slice (c) Phase 6 sub-plan template)

Each service consuming this SSOT files a sub-plan at `plans/active/wave4_emission_rollout_<service>_<YYYY_MM_DD>.md`
with this structure (Citadel-Grade Planning Standards):

1. **Pre-audit blast radius** — identify every `record_captured(` callsite in the service, classify as raw-capture (no
   wire-in needed) vs derived-output (wire-in required).
2. **Phased DAG** — group emission boundaries by data_type slice (`:current` vs `:historical`); declare phase
   dependencies + QG gates.
3. **No technical debt** — old inline `record_captured` calls fully replaced by the publish-boundary wrapper; no compat
   shims.
4. **Parallelization** — when N data_types are independent (`ohlcv_1m:current` + `ohlcv_1m:historical` +
   `book_snapshot_5:current` + ...), fan-out via parallel Task sub-agents per the workspace
   sub-agent-with-mandatory-rules pattern.
5. **Success criteria** — every `(service, output_data_type)` slice has a seed row in `SERVICE_OUTPUT_POLICIES`; every
   emission boundary wires `publish_with_policy()` / `publish_with_manifest_lookup()`; service QG green; per-service
   plan checkbox flipped with commit-sha evidence.
6. **Downstream consumer updates** — `SERVICE_OUTPUT_POLICIES` seed additions go in UAC with a `__all__` re-export per
   the Citadel import rules.
7. **SSOT** — this codex doc + the UAC `SERVICE_OUTPUT_POLICIES` dict.

## Composes with

- `codex/02-data/availability-manifest-and-data-status.md` — the 4-state manifest layer this builds on.
- `codex/02-data/honest-absence-downstream-handling.md` — downstream NaN-handling tolerances per consumer class.
- `cursor-configs/CLAUDE.md` § "Service-output emission policy" — key-rule entry pointing here.
- `plans/active/writegate_honest_coverage_endtoend_2026_05_06.md` slices (a) + (b) + (c) — the architecture plan.
- `plans/active/manifest_schema_final_gate_2026_05_09.md` Phase 1-2 — owns the v8 manifest schema columns
  (`service_emission_state` + `last_emission_decision_at` + `expected_window_completeness_fraction`) which complement
  the in-band parquet-row columns this doc describes.
