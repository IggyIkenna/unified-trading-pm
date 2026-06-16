---
scope: [engineer, admin]
last_reviewed: 2026-06-11
---

# `pipeline_mode` Column — Batch/Live Reconciliation

> **STATUS** — Documents the `pipeline_mode` manifest column + the source-aware `{mode}_{source}[_{transport}]` model
> (G0 standardisation 2026-06-05; operator R4 transport rule 2026-06-07). On-disk partition is IN PROGRESS as a named
> rider per AG L3 walk (see § "On-disk partition" below). Implementation plan:
> [`plans/active/pipeline_mode_implementation_2026_05_28.md`](../../plans/active/pipeline_mode_implementation_2026_05_28.md);
> source-aware model SSOT:
> [`plans/active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md`](../../plans/active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md).

## What `pipeline_mode` is

`pipeline_mode` is a `StrEnum` column on every availability manifest row that identifies **which pipeline wrote it** — a
batch source (Tardis archive, Databento, onchain RPC, etc.), the intraday replay gap-fill, or a live feed. It enables
batch ↔ live reconciliation via `GROUP BY pipeline_mode` over the same manifest without a separate table.

**Canonical form is SOURCE-AWARE (M1 / G0 standardisation):** `{mode}_{source}[_{transport}]` where:

- `mode ∈ {batch, live, replay}` — the reconciliation axis (`Mode` enum). `replay` is the intraday gap-fill tier (always
  the MIDDLE of mode-contextual precedence — see § precedence below).
- `source` is the **VENDOR ONLY** (e.g. `databento`, `tardis`, `onchain_rpc`, `hyperliquid`) — transport is **NEVER**
  glued into it (operator R4 2026-06-07; the retired `hyperliquid_rest` source was that antipattern — now
  `source=hyperliquid` + `transport=rest`).
- `[_{transport}]` is an OPTIONAL trailing segment in the `pipeline_mode` value **only where a source genuinely runs
  more than one transport for the SAME shard** (else omitted — no noise). No registered source does today, so no member
  carries the suffix yet. The transport itself is ALWAYS carried in a separate `transport` manifest COLUMN regardless
  (see § "Transport axis" below).

Closed-set rule: a `live_<source>` / `replay_<source>` member exists **iff** that source declares `Mode.LIVE` /
`Mode.REPLAY` capability (`SOURCE_MODE_CAPABILITY`, enforced by `test_source_mode_capability.py`). `live_websocket` is a
**TRANSITIONAL alias** kept for the not-yet-migrated live shards — its migration to `live_<source>` is the gated next
tranche.

The canonical enum is `unified_api_contracts.canonical.crosscutting.pipeline_mode.PipelineMode`:

| Value                                                                           | Source / meaning                                  |
| ------------------------------------------------------------------------------- | ------------------------------------------------- |
| `batch_tardis`                                                                  | Tardis archive (default CeFi; `flat_file`)        |
| `batch_databento`                                                               | Databento (default TradFi)                        |
| `batch_hyperliquid`                                                             | Hyperliquid (vendor; `transport=rest` in column)  |
| `batch_onchain_rpc`                                                             | EVM / Solana native RPC (default DeFi)            |
| `batch_onchain_subgraph`                                                        | DeFi subgraph (Uniswap etc.)                      |
| `batch_polymarket_clob`                                                         | Polymarket CLOB + Kalshi                          |
| `batch_polymarket_gamma_api`                                                    | Polymarket Gamma API                              |
| `batch_chainlink`                                                               | Chainlink oracle                                  |
| `batch_pyth_hermes`                                                             | Pyth Hermes (Solana)                              |
| `batch_solana_rpc` / `batch_helius_rpc`                                         | Solana native / Helius enriched RPC               |
| `batch_instruments_service`                                                     | Instruments service internal                      |
| _(…more batch values in PipelineMode)_                                          |                                                   |
| `live_<source>` (e.g. `live_databento`, `live_onchain_rpc`, `live_hyperliquid`) | source-aware live feed (M1)                       |
| `replay_<source>` (e.g. `replay_onchain_rpc`, `replay_databento`)               | intraday replay gap-fill (M1)                     |
| `live_websocket`                                                                | TRANSITIONAL alias — not-yet-migrated live shards |

## How to resolve `pipeline_mode` at write time

Use the UTL SSOT helper — never hardcode string literals:

```python
from unified_trading_library import resolve_pipeline_mode

pm = resolve_pipeline_mode(
    service="market-tick-data-service",
    mode="batch",          # or "live"
    venue="BINANCE",       # optional — venue override wins
    asset_group="cefi",    # optional — consulted via SOURCE_PRIORITY
    data_type="trades",    # optional — paired with asset_group
)
# → PipelineMode.BATCH_TARDIS
```

Resolution order:

1. `mode="live"` → the source-aware `LIVE_<SOURCE>` if the resolved source declares live capability, else the
   transitional `LIVE_WEBSOCKET` alias (until the `live_<source>` object migration lands)
2. Venue override (e.g. `HYPERLIQUID` → `BATCH_HYPERLIQUID` — vendor only, transport in the column)
3. UAC `read_with_source_priority(asset_group, data_type)` → primary source's mode
4. Per-service fallback (`instruments-service` → `BATCH_INSTRUMENTS_SERVICE`, etc.)
5. `ValueError` if nothing matches — add to `_VENUE_OVERRIDES` or UAC SOURCE_PRIORITY

## Transport axis (the `[_{transport}]` segment + the `transport` column)

`transport ∈ {rest, websocket, flat_file}` (`Transport` enum) is a **separate axis from `source`** (the vendor). Two
ratified rules (operator R4 2026-06-07):

1. **Path-key suffix** — the `[_{transport}]` segment appears in the `pipeline_mode` value (and thus the on-disk
   `pipeline_mode=` hive key) **only where a source genuinely runs >1 transport for the SAME shard** (else omitted — no
   noise). No registered source does today, so `transport_of(mode)` returns `None` for every current member.
2. **`transport` column** — ALWAYS populated on every manifest row, regardless of the suffix, via
   `default_transport_for_source(source)` unless the writer is passed an explicit value. `tardis` T+1 archives are
   `flat_file`; every other batch source is REST-family (`rpc` / `graphql` / `sse` all resolve over HTTP → `rest`).
   Live-websocket transport for the gated `live_<source>` tranche is stamped explicitly by live writers.

Helpers (all in `unified_api_contracts.canonical.crosscutting.pipeline_mode`): `transport_of(mode)`,
`default_transport_for_source(source)`, `source_string_for(mode)` (strips `{mode}_` prefix AND any transport suffix →
vendor only), `is_batch` / `is_live` / `is_replay`.

## How to derive `pipeline_mode` for backfill

For existing rows (NULL `pipeline_mode`), use `derive_pipeline_mode_for_row()`:

```python
from unified_trading_library import derive_pipeline_mode_for_row

pm = derive_pipeline_mode_for_row(
    venue="BINANCE",
    asset_group="cefi",
    data_type="trades",
    pipeline_mode_col=existing_row_value,  # idempotent: returned as-is if valid
)
# → PipelineMode.BATCH_TARDIS, or None if undecidable
```

The one-shot backfill script lives at `unified-trading-pm/scripts/migration/backfill_pipeline_mode.py`.

## Batch ↔ live reconciliation pattern

Stage 0 of `batch-live-reconciliation-service` compares the batch vs live sides of the manifest for each date by
filtering on `pipeline_mode` (use the helpers, not raw string matching):

- **Batch side**: any row where `is_batch(mode)` (`pipeline_mode` starts with `batch_`)
- **Live side**: any row where `is_live(mode)` — both the transitional `live_websocket` alias AND the source-aware
  `live_<source>` members
- **Replay side**: any row where `is_replay(mode)` (`replay_<source>`) — the intraday gap-fill tier, reconciled into
  whichever mode-contextual precedence the consumer reads (M4: a live consumer reads `live > replay > batch`; a batch
  consumer reads `batch > replay > live`)

```
manifest rows (same bucket, same date)
├── batch_<source> rows  → batch_status, batch_reason
├── replay_<source> rows → replay_status, replay_reason  (intraday gap-fill)
└── live_<source> / live_websocket rows → live_status, live_reason

Agreement rules:
  both captured                           → OK
  both empty_confirmed, same reason       → OK (agreed expected gap)
  both empty_confirmed, different reasons → FLAG (reason disagreement)
  one captured, other attempted_failed    → FLAG (asymmetric failure)
  one or both absent from manifest        → skip (fail-open)
  unknown combination                     → log warning, no flag
```

## Ratified target — the full M1–M8 reconciliation contract

> Settled contract (operator-ratified 2026-06-05/07; codified per M-COORD-1/R6-codex 2026-06-11). The full target-design
> narrative lives in [`pipeline-mode-partition.md`](pipeline-mode-partition.md) § "Ratified TARGET design — live/replay
> (M1–M8 settled contract)" — plans reference codex, not vice versa. The reconciliation-service-facing slice:

- **M2×M3 guardrail**: whether a `(source, data_type)` can run live/replay is a FACT in UAC — per-`(source, data_type)`
  `modes_for()` (LANDED — M2-REFINEMENT, unified-api-contracts@a56a7fc2, derived from `SourceCapability.operations`;
  refines the coarse `SOURCE_MODE_CAPABILITY`/`modes_for_source`); `could_exist(shard, mode)` now composes
  `modes_for(source, data_type)` and bounds every reconciliation + coverage denominator — never flag a shard for a mode
  no source can serve for that data_type.
- **M4 `select_for_mode`** (this service is the HOME): the live read-path resolver picks which mode's VALUE a consumer
  reads — live consumer `live > replay > batch`, batch consumer `batch > replay > live`, replay always the middle tier.
  The data-status union stays mode-agnostic (shipped consumer-side, `deployment-api@4dd2575`).
- **M6 startup/continuity gate** (this service + strategy live-flip + MTDS startup): the `[batch-cutoff → now]` tail per
  shard resolves to exactly one of — autostart `replay_<source>` (replay-capable) / assert live already running
  (live-only) / wait-refuse-configured-gap (batch sole SSOT).
- **M7 autonomous recovery**: alerting detects `(batch-stopped + no-live + replay-capable)` and FIRES the replay itself;
  per-shard "gaps-OK" is DR config, never a default.
- **T+1 batch≈live reconciliation + live TTL**: after batch lands, confirm batch ≈ live within a tolerance, then TTL the
  now-redundant `live_<source>` cells (batch is the durable SSOT; long-lived `replay_<source>` stays where batch never
  existed). Knobs: tolerance + TTL horizon.
- **M8 cadence**: a manifest COLUMN + deployment-registry `run_class` (`one_off_backfill`/`t1_daily`/
  `scheduled_recurring`/`continuous_live`/`recovery_replay`) — NEVER a path key, never a reconciliation stratum: the
  reader unions over `pipeline_mode` only; ops/UI slice by cadence.

**Gated tranche (`M1-BREAKING`)**: the `live_websocket` → `live_<source>` object/writer/reader migration, the
`replay_<source>` write path, the `select_for_mode` resolver, the M6/M7 gates, and the T+1 TTL all land behind the M1/M2
foundation — until then live writes the transitional alias and reconciliation treats `live_websocket` as live.

## NOT NULL constraint status

As of 2026-05-28, `pipeline_mode` allows NULL in the schema — ~38M legacy rows written before Phase 4.MTDS (2026-05)
have NULL. The NOT NULL constraint will be enforced after the backfill verifies clean
(`SELECT count(*) WHERE pipeline_mode IS NULL = 0` per bucket).

## On-disk partition (IN PROGRESS as named rider per AG L3 walk)

Adding `pipeline_mode=` as a hive partition key on disk is **IN PROGRESS** — re-scoped from "Phase 5 DEFERRED" to a
named **rider** inside each asset-group's L3 single-walk per
`plans/active/pipeline_mode_partition_migration_2026_06_01.md`. Reads continue to filter via column-scan (low
cardinality, ~10 values) until each per-bucket rider completes.

**Per-bucket rider coverage** (as of 2026-06-01):

| Bucket / asset-group      | Rider status                   | Notes                                      |
| ------------------------- | ------------------------------ | ------------------------------------------ |
| `market-data-tick-cefi`   | In L3 walk plan                | Rider confirmed in AG cefi L3 walk scope   |
| `market-data-tick-defi`   | In L3 walk plan                | Rider confirmed in AG defi L3 walk scope   |
| `market-data-tick-tradfi` | In L3 walk plan                | Rider confirmed in AG tradfi L3 walk scope |
| `market-data-tick-sports` | In L3 walk plan                | Rider confirmed in AG sports L3 walk scope |
| `instruments-store-*`     | **Pending** — not yet in scope | instruments bucket rider not yet scheduled |

See: [`pipeline-mode-partition.md`](pipeline-mode-partition.md) for the Phase 3 migration history (2026-05-19
hive-partition walk).

## Cross-links

- [`availability-manifest-and-data-status.md`](availability-manifest-and-data-status.md)
- [`contracts-scope-and-layout.md`](contracts-scope-and-layout.md)
- [`pipeline-mode-partition.md`](pipeline-mode-partition.md) — on-disk partition history
