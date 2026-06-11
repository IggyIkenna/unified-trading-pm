---
scope: [engineer, admin]
created: 2026-05-14
plan: plans/active/batch_live_symmetry_2026_05_10.md Tab 1
last_reviewed: 2026-05-17
---

# CeFi Batch/Live Architecture

> Per-asset-group narrative for `asset_group=cefi`. Cross-cutting batch=live invariant lives in
> [`batch-live-architecture.md`](batch-live-architecture.md). This doc covers the CeFi-specific shape: venue list,
> matcher pattern, shard atomicity, and the DeFi hedge-leg integration.

---

## §1 CeFi venues in scope

Seven venues are in the CeFi pipeline:

| Venue       | Code        | Perp-pair types        | Margin options           |
| ----------- | ----------- | ---------------------- | ------------------------ |
| Binance     | BINANCE     | USDT-M + COIN-M perps  | USDT / BTC collateral    |
| Bybit       | BYBIT       | Linear + inverse perps | USDT / UTA portfolio     |
| OKX         | OKX         | USDT-M + COIN-M perps  | USDT / wstETH collateral |
| Deribit     | DERIBIT     | Options + perps        | BTC / ETH / stETH        |
| Kraken      | KRAKEN      | Multi-asset futures    | Multi-collateral         |
| Hyperliquid | HYPERLIQUID | USDC perps             | USDC                     |
| Aster       | ASTER       | USDC perps             | USDC                     |

**Source of truth**: UAC `registry/capability_declarations/_cefi.py` — each venue's supported instruments + margin modes
are declared there and read at startup by instruments-service.

---

## §2 Batch/live symmetry — CeFi-specific shape

The core invariant from [`batch-live-architecture.md §1`](batch-live-architecture.md) applies: 99% of the code path is
identical. The seams for CeFi:

| Seam            | Batch                                  | Live                                         |
| --------------- | -------------------------------------- | -------------------------------------------- |
| Data source     | Tardis / Databento tick Parquet on GCS | WebSocket feed (MTDS → Redis Stream → MDPS)  |
| Feature compute | Load feature Parquet from GCS          | Embedded UTL `feature_calculator` in-process |
| ML inference    | Load prediction Parquet from GCS       | Subscribe to prediction Redis/PubSub topic   |
| Execution fills | `MatchingEngine` (L2Matcher)           | Real venue REST/WS order execution           |

The only seam that materially differs is execution fills. Every other difference is transport-layer, not business-logic.

---

## §3 Matching engine — L2Matcher (CeFi)

CeFi fills in batch mode route through `L2Matcher` in `execution-service/execution_service/matching_engine/`.

- **Model**: order-book depth simulation with 5 price levels (L1/L2).
- **Fill logic**: aggressor-side fill at best-bid/ask ± level walk. Commission = maker/taker schedule per venue.
- **Latency model**: venue-latency draw from per-venue normal distribution (mean/std sourced from empirical Tardis
  latency feeds).
- **`BatchExecutionMode.BENCHMARK`**: bypasses L2Matcher entirely — always fills at the requested price, zero
  commission, zero slippage (strategy alpha isolation).
- **`BatchExecutionMode.SIMULATED`**: routes through L2Matcher (execution alpha measurement).

The `BatchExecutionMode` enum lives at `unified_api_contracts.internal.execution.BatchExecutionMode` (SSOT). Dispatch in
`node_builder.py` selects matcher at batch-run start; live mode always uses real venue fills.

---

## §4 Shard atomicity — CeFi

CeFi shard atom is `(asset_group=cefi, data_type, venue, date)`.

**CRITICAL empty-record rules**:

- CeFi shards CANNOT receive `record_empty(reason=EXPECTED_INSTRUMENT_NOT_LISTED)` at the instrument-day grain — cefi
  venues are always-open (24/7 trading). The only legitimate `empty_confirmed` reasons for cefi are:
  - `EXPECTED_HOLIDAY` — venue closed (rare; some observe holidays)
  - `EXPECTED_WEEKEND` — venue weekend closure (for futures settlement windows only)
  - `EXPECTED_PRE_VENUE_LAUNCH` — instrument not yet listed on the venue
  - `EXPECTED_PRE_GENESIS_CHAIN` — DeFi-adjacent CeFi instrument pre-genesis
  - `EXPECTED_PARTIAL_HALF_DAY` — partial trading day
- Any other absence MUST be `record_failed(error=...)` — NOT `record_empty`.

**Shard identity propagation**: the 5-pillar shard atom must be identical across writer atomicity → manifest row key →
data-status display → downstream preflight gate → deployment-UI drilldown. Drift between any two is a silent correctness
bug. SSOT: [`../epics/infrastructure_master.md`](../../plans/epics/infrastructure_master.md).

---

## §5 DeFi hedge-leg integration (CeFi as DeFi counterpart)

DeFi strategies are NOT on-chain only. The hedge/short leg of every DeFi archetype runs on CeFi perp venues. CeFi
adapters are therefore in the live execution path for DeFi archetypes:

| Archetype                    | On-chain leg     | CeFi hedge venues                                       | Margin type   |
| ---------------------------- | ---------------- | ------------------------------------------------------- | ------------- |
| `carry_staked_basis`         | LST stake / lend | Bybit UTA (stETH), Deribit (stETH), OKX (wstETH), DRIFT | LST_AS_MARGIN |
| `arbitrage_price_dispersion` | DEX spot         | All 7 venues (USDC margin)                              | USDC          |

The `LST_AS_MARGIN` eligibility criterion is archetype-driven, not venue-level. Consult
[`../09-strategy/architecture-v2/archetypes/`](../09-strategy/architecture-v2/archetypes/) for per-archetype margin +
venue eligibility matrix.

**Batch/live symmetry for hedge legs**: the CeFi matching engine (`L2Matcher`) simulates the hedge-leg fills in batch
mode at the same fidelity as the long-leg DeFi AMMMatcher. The batch=live seam remains identical — only the fill source
(matching engine vs real venue) differs. Neither leg gets special-cased in the strategy engine.

---

## §6 Live pipeline timing — CeFi

CeFi ticks follow the same MTDS → Redis Stream → MDPS → features-service cascade as other asset groups.

- **MTDS** subscribes to WebSocket feeds per venue + emits `streaming.cefi.candle_boundary_crossed` at UTC-aligned
  boundaries per the
  [`../05-infrastructure/live-pipeline-architecture.md`](../05-infrastructure/live-pipeline-architecture.md) cascade
  contract.
- **MDPS** runs in asset-scoped-colocated topology: one MDPS VM per `(asset_group=cefi, venue)` pair.
- **features-service**: `delta_one`, `volatility`, `cross_instrument` families consume CeFi candles.

The UTC-alignment rule (§10.1 of `batch-live-architecture.md`) applies: MTDS never emits partial windows at startup.

---

## §7 Anti-patterns

- Don't build a standalone CeFi-only backtest engine — route through execution-service MatchingEngine.
- Don't add `pipeline_mode=cefi_live` or `pipeline_mode=cefi_batch` — `pipeline_mode` is the SOURCE-AWARE
  `{mode}_{source}[_{transport}]` closed set (cefi: `batch_tardis` / `batch_hyperliquid` / `live_<venue>` /
  `replay_<venue>`; `live_websocket` is the transitional alias until the gated `M1-BREAKING` tranche) — never an
  asset_group-glued or coarse value (see
  [`../02-data/pipeline-mode-partition.md`](../02-data/pipeline-mode-partition.md) § "Ratified TARGET design").
- Don't write `if asset_group == "cefi": use_l2_matcher` — matcher dispatch is on `BatchExecutionMode`, not on
  asset_group. CeFi + TradFi both use L2Matcher; DeFi uses AMMMatcher; Sports uses L0Matcher.
- Don't emit `record_empty(reason=EXPECTED_INSTRUMENT_NOT_LISTED)` for cefi at instrument-day grain — cefi is 24/7.
  Missing = `record_failed`, not `record_empty`.
- Don't treat LST_AS_MARGIN venues as cefi-only — they are DeFi archetype hedge legs routed through CeFi venues.

---

## §9 — CeFi adapter: expiry-window contract + 401≠honest-absence (2026-05-27)

> Full codex SSOT:
> [`../02-data/honest-absence-downstream-handling.md §7`](../02-data/honest-absence-downstream-handling.md). Summary
> here for CeFi adapter authors.

### Expiry-window pre-request filter (MANDATORY)

CeFi dated instruments (OKX, Deribit, Kraken futures/options) carry `available_from` / `available_to_datetime` in
`InstrumentRecord`. The adapter MUST filter the `(instrument, date)` request matrix against this window BEFORE making
any Tardis API call:

```python
# In the CeFi Tardis download expansion loop:
if instr.available_from and date < instr.available_from.date():
    manifest.record_empty(reason=EmptyConfirmedReason.EXPECTED_INSTRUMENT_NOT_LISTED)
    continue
if instr.available_to_datetime and date > instr.available_to_datetime.date():
    manifest.record_empty(reason=EmptyConfirmedReason.EXPECTED_INSTRUMENT_DELISTED)
    continue
```

**Why**: Tardis code 140 (`"Data available only up to <date>"`) is a predictable 400 for out-of-window requests — ~1,250
per OKX VM per backfill window. These are NOT adapter errors; they are the wrong `(instrument, date)` pairs. Record
`expected_unattempted` before the call, not `attempted_failed` after.

### 401 — blocked credentials, NOT honest absence

If Tardis returns HTTP 401 (expired key / missing key), record `attempted_failed` with `CLASSIFIED_VENUE_ERROR`:

```python
except VenueAuthError:  # classified from HTTP 401 by classify_venue_error()
    manifest.record_failed(error=classify_venue_error(exc))  # → attempted_failed
    # Do NOT record_empty — data exists, key is temporarily invalid
```

Rationale: a 401-stamped `empty_confirmed` row looks like a calendar gap to downstream consumers and will never be
retried after key renewal. `attempted_failed` keeps the cell in the "retryable" queue.

---

## §8 Cross-references

- **Batch/live invariant (global)**: [`batch-live-architecture.md`](batch-live-architecture.md) §1-§4
- **Matching engine + L2Matcher**: [`batch-live-architecture.md §5`](batch-live-architecture.md)
- **AMMMatcher (DeFi leg)**: [`amm-slippage-simulation.md`](amm-slippage-simulation.md)
- **Live pipeline cascade**:
  [`../05-infrastructure/live-pipeline-architecture.md`](../05-infrastructure/live-pipeline-architecture.md)
- **Replay subsystem**: [`../05-infrastructure/replay-subsystem.md`](../05-infrastructure/replay-subsystem.md)
- **Pipeline-mode partition**: [`../02-data/pipeline-mode-partition.md`](../02-data/pipeline-mode-partition.md)
- **DeFi archetype hedge legs**:
  [`../09-strategy/architecture-v2/archetypes/`](../09-strategy/architecture-v2/archetypes/)
- **BatchExecutionMode**: `unified_api_contracts.internal.execution.BatchExecutionMode`
- **Shard-granularity SSOT**: `plans/epics/infrastructure_master.md`
- **Empty-record rules**:
  [`../02-data/availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md)
- **CeFi expiry-window + 401 contract**:
  [`../02-data/honest-absence-downstream-handling.md §7`](../02-data/honest-absence-downstream-handling.md)
