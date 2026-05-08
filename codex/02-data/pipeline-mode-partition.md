---
scope: [engineer, admin]
---

# `pipeline_mode` Hive Partition

> **STATUS** — Documents the `pipeline_mode={batch_*, live_websocket, ...}` hive partition column added across every
> parquet on disk during the bundled GCS migration on 2026-05-XX. Migration owner:
> [`plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md`](../../plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md).
> If this doc disagrees with the active plan, the plan wins.

## Shipped progress (2026-05-08, Tab 3 GCS migration cluster)

| Phase                                                   | Status      | Commit(s)                                                                       |
| ------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------- |
| 0 — pre-audit doc (operator-runnable on same-region VM) | ✅ shipped  | `unified-trading-pm@0cc633c8` (doc) + `@12483f5b` (plan flip)                   |
| 1A — UAC `PipelineMode` SSOT + closed-set round-trip    | ✅ shipped  | `unified-api-contracts@8bc3f2a`                                                 |
| 1B — UTL `ManifestWriter` `pipeline_mode` kwarg + tests | ✅ shipped  | `unified-trading-library@87134364`                                              |
| 1C — UAC `SOURCE_PRIORITY` `pipeline_mode` field        | ✅ shipped  | `unified-api-contracts@6a8529f` + `unified-trading-pm@53c498c5`                 |
| 2 — Canonical migration script + 23 unit tests          | ✅ shipped  | `unified-trading-pm@5a3c360a` + `@cc6fe4ce` (plan flip)                         |
| 5.1 — UTL `read_manifest_with_source_priority` reader   | ✅ shipped  | `unified-trading-library@52f123d6` + `unified-trading-pm@2a0d105d` (annotation) |
| 3 — Operator-gated VM execution                         | ⏳ pending  | Operator runs after pre-audit results (§§(b)(c)(d)(e)(h) of pre-audit doc).     |
| 4 — Workspace-wide consumer sweep                       | ⏳ pending  | Parallel with Phase 3.                                                          |
| 5.2 / 5.3 — MTDS/MDPS path probers + Sports/DeFi paths  | ⏳ pending  | Follow-up sub-agents.                                                           |
| 6 — Residual phantom cleanup (post-Phase-3.6)           | ⏳ pending  | Sequential after Phase 3.6.                                                     |
| 8 — Reader fallback removal (T+30d, ~2026-06-15)        | ⏸ deferred | "no double SSOT" rule once `READER_FELL_BACK_TO_LEGACY_PATH` count = 0 / 7d.    |
| 9 — Final workspace-wide QG sweep                       | ⏳ pending  | Sequential after Phase 6.                                                       |

## TL;DR

`pipeline_mode` is the outermost hive partition column added to every parquet path:

```
gs://{pid}-raw-tick/raw_tick_data/by_date/day=YYYY-MM-DD/pipeline_mode=live_websocket/asset_group=cefi/venue=binance/...
```

Same parquet schema, same `available_at` semantics, same row-key shape across batch and live. UAC `SOURCE_PRIORITY` does
the live-vs-batch fan-in at read time. Manifest treats every `(pipeline_mode, asset_group, venue, data_type, day)` as a
distinct row with the existing 4-state capture taxonomy. Reconciliation is a SQL `GROUP BY pipeline_mode` over the same
`_index/availability_index.parquet`.

## Why a partition (not a schema column)

Three reasons:

1. **Zero schema migration cost on existing readers.** Hive partition columns are handled by the parquet path probe;
   readers that don't filter on `pipeline_mode` see all rows transparently (subject to the reader-fallback chain during
   the migration window).
2. **Partition pruning** — readers querying batch-vs-live reconciliation efficiently scan only the relevant prefix.
3. **Live writes can land alongside batch writes** in the same bucket without conflict — the `pipeline_mode=` segment
   keeps them physically separated on disk while logically reconcilable.

## Closed-set values (UAC `PipelineMode` StrEnum)

| Value                         | Source                                                                       |
| ----------------------------- | ---------------------------------------------------------------------------- |
| `batch_databento`             | Databento bulk + replay APIs (CME GLBX.MDP3 trades, OHLCV)                   |
| `batch_tardis`                | Tardis CeFi historical ticks                                                 |
| `batch_ccxt`                  | CCXT REST batch (per-instrument T+1 reconcile)                               |
| `batch_barchart`              | VIX 15m historical preload (2020-01-02 → 2025-11-12)                         |
| `batch_yahoo`                 | VIX 15m rolling window (last 60d) + tradfi ETFs                              |
| `batch_api_football`          | api_football fixtures / events / lineups / stats                             |
| `batch_footystats`            | footystats odds / xG                                                         |
| `batch_understat`             | understat xG / shot maps                                                     |
| `batch_transfermarkt`         | transfermarkt player values                                                  |
| `batch_soccer_football_info`  | SFI progressive stats                                                        |
| `batch_open_meteo`            | open-meteo weather (per fixture)                                             |
| `batch_odds_api`              | odds_api closing-line + horizon snapshots                                    |
| `batch_polymarket_historical` | Polymarket CLOB historical                                                   |
| `batch_kalshi_historical`     | Kalshi historical                                                            |
| `batch_lighter_candles`       | Lighter `/candles` historical (per dex_perp_onboarding 2026-05-07)           |
| `batch_pacifica_kline`        | Pacifica `/kline` historical                                                 |
| `batch_databento_replay`      | Databento used by the replay-cascade subsystem                               |
| `live_websocket`              | Live websocket-streaming pipeline (MTDS / MDPS / features-service live mode) |

**Source-of-truth rule**: every UAC `SOURCE_PRIORITY` entry MUST have a corresponding `PipelineMode` value, and vice
versa. Unit test in `unified-api-contracts/tests/unit/test_pipeline_mode.py` enforces the round-trip.

## Reader behaviour

`UAC.SOURCE_PRIORITY` resolution at read time:

1. Stratify rows by `pipeline_mode` group (live vs each batch source).
2. Within each stratum, apply the existing `priority` ordering.
3. **Live always wins for dates where live exists**; batch wins where it doesn't.

This makes batch-vs-live reconciliation straightforward: pivot the same query by `pipeline_mode` and diff the per-shard
output. See `live_pipeline` Phase 12 for the full reconciliation gate criteria.

## Migration history

Bundled migration 2026-05-XX per
[`gcs_migration_bundle_pipeline_mode_2026_05_08`](../../plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md).
Three migrations rode together:

1. Add `pipeline_mode=` segment to every existing batch parquet, applying the source-priority entry's value (e.g.
   `batch_databento` for Databento-written parquets, `batch_tardis` for Tardis).
2. Finish the `category=` → `asset_group=` rekey CLAUDE.md previously preserved as legacy-with-fallback.
3. Sweep up the 5 drift axes from the 2026-05-04 phantom-audit incident (path-prefix, instrument_type casing, schema-4
   empty instrument_type, chain-bundle equivalence, etc.).

The manifest was rewritten ONCE during the bundle — readers continue to function via the fallback chain (see below).

## Reader fallback chain (≤30 days post-migration; deleted 2026-06-15)

UTL `read_manifest_with_source_priority(...)` + MTDS / MDPS path probers + sports `candidate_parquet_paths` helper try
canonical path first, then fall back through:

1. Without `pipeline_mode=` segment (pre-migration shape).
2. With legacy `category=` instead of `asset_group=`.
3. With legacy `day=*/` prefix instead of `raw_tick_data/by_date/day=*/`.
4. Combinations of the above.

Each fallback hit emits a `READER_FELL_BACK_TO_LEGACY_PATH` event so we can monitor when fallbacks are no longer needed.
Fallback paths are **deleted T+30 days post-migration** per workspace "no double SSOT" rule. Tracked in the migration
plan's Phase 8.

## Anti-patterns

- Don't keep the `category=` reader fallback long-term. Phase 8 of the migration plan deletes it 2026-06-15.
- Don't introduce a new `pipeline_mode` value without adding a corresponding `SOURCE_PRIORITY` entry. The round-trip
  unit test will fail.
- Don't use `pipeline_mode=replay_*`. The replay subsystem writes to `pipeline_mode=live_websocket` with original-time
  `available_at` (per [`../05-infrastructure/replay-subsystem.md`](../05-infrastructure/replay-subsystem.md)).
- Don't write to manifest without the explicit `pipeline_mode=` kwarg post-migration. The default value is removed after
  Phase 4 sweep is grep-clean — explicit-or-fail.

## Cross-references

- Plan:
  [`gcs_migration_bundle_pipeline_mode_2026_05_08`](../../plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md)
- Foundation: [`availability-manifest-and-data-status.md`](./availability-manifest-and-data-status.md) — manifest
  schema + 4-state taxonomy + reason taxonomy.
- Sibling: [`../05-infrastructure/live-pipeline-architecture.md`](../05-infrastructure/live-pipeline-architecture.md) —
  consumer of the new partition for live-mode writes.
- Sibling: [`../05-infrastructure/replay-subsystem.md`](../05-infrastructure/replay-subsystem.md) — replay writes also
  go to `pipeline_mode=live_websocket`.
