---
scope: [engineer, admin]
last_reviewed: 2026-05-19
---

# `pipeline_mode` Hive Partition

> **STATUS** — Documents the `pipeline_mode` hive partition column added across every parquet on disk during the bundled
> GCS migration on 2026-05-19. Migration owner:
> [`plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md`](../../plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md).
> If this doc disagrees with the active plan, the plan wins.
>
> **CANONICAL FORM (M1/C-TRANSPORT, operator-ratified 2026-06-07)**: `pipeline_mode = {mode}_{source}[_{transport}]`
> where `mode ∈ {batch, live, replay}`, `source` is the VENDOR only, and `[_{transport}]` is an OPTIONAL trailing
> segment present in the path key **only** where a source genuinely runs >1 transport for the SAME shard (else omitted).
> See § "Source-aware modes + transport" below — this SUPERSEDES the earlier batch-only `{batch_*, live_websocket}`
> framing (`live_websocket` is now a transitional alias, and `replay_<source>` is a real mode). SSOT:
> [`plans/active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md`](../../plans/active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md).

## Shipped progress (updated 2026-05-19 post-Phase-3 run)

| Phase                                                       | Status        | Commit(s)                                                                       |
| ----------------------------------------------------------- | ------------- | ------------------------------------------------------------------------------- |
| 0 — pre-audit doc (operator-runnable on same-region VM)     | ✅ shipped    | `unified-trading-pm@0cc633c8` (doc) + `@12483f5b` (plan flip)                   |
| 1A — UAC `PipelineMode` SSOT + closed-set round-trip        | ✅ shipped    | `unified-api-contracts@8bc3f2a`                                                 |
| 1B — UTL `ManifestWriter` `pipeline_mode` kwarg + tests     | ✅ shipped    | `unified-trading-library@87134364`                                              |
| 1C — UAC `SOURCE_PRIORITY` `pipeline_mode` field            | ✅ shipped    | `unified-api-contracts@6a8529f` + `unified-trading-pm@53c498c5`                 |
| 2 — Canonical migration script + 23 unit tests              | ✅ shipped    | `unified-trading-pm@5a3c360a` + `@cc6fe4ce` (plan flip)                         |
| 3 — VM fleet execution (31 VMs, all 5 asset_groups)         | ✅ complete   | 2026-05-19 13:52→16:01 UTC; all 31 VMs TERMINATED exit 0. No data loss.         |
| 4 — Workspace-wide consumer sweep                           | ✅ complete   | All production callsites pass explicit `pipeline_mode=`. No gaps found.         |
| 5.1 — UTL `read_manifest_with_source_priority` reader       | ✅ shipped    | `unified-trading-library@52f123d6` + `unified-trading-pm@2a0d105d` (annotation) |
| 5.2 — MTDS/MDPS path probers                                | ✅ shipped    | `market-tick-data-service@33b2ae5` (2026-05-19)                                 |
| 5.3 — Sports/DeFi `candidate_parquet_paths` extension       | ✅ shipped    | `unified-api-contracts@fefd720` (2026-05-19)                                    |
| Axis-10 — Reconciler pipeline_mode= prefix fix              | ✅ shipped    | `instruments-service@8accb30` (2026-05-19) — see pre/post counts below          |
| 3.6 — Post-migration phantom gate (re-audit w/ Axis-10 fix) | ✅ complete   | prediction ✅ 0 / sports ✅ 0 / tradfi ✅ 0 / defi ✅ 0 / cefi ✅ 0             |
| 6 — Residual phantom cleanup                                | 🚫 not needed | Axis-10 false positives; parquets exist at new paths. DO NOT run `--apply`.     |
| 8 — Reader fallback removal (T+30d, ~2026-06-15)            | ⏸ deferred    | "no double SSOT" rule once `READER_FELL_BACK_TO_LEGACY_PATH` count = 0 / 7d.    |
| 9 — Final workspace-wide QG sweep                           | ⏳ pending    | Sequential after Phase 3.6 operator sign-off.                                   |

### Phase 3 migration: pre/post phantom counts (2026-05-19)

| Asset group | Pre-migration (Gate 3, 2026-05-17) | Post-migration (initial audit)  | Root cause           | Post-Axis-10-fix re-audit |
| ----------- | ---------------------------------- | ------------------------------- | -------------------- | ------------------------- |
| sports      | 0 phantoms / 559,961 real          | 0 phantoms ✅                   | n/a — UAC dispatcher | 0 phantoms ✅ confirmed   |
| prediction  | 0 phantoms / 14,403 real           | 14,403 phantoms 🔴 FALSE POS    | Axis-10 (reconciler) | 0 phantoms ✅ confirmed   |
| tradfi      | 0 phantoms / 245,907 real          | 245,907 phantoms 🔴 FALSE POS   | Axis-10 (reconciler) | 0 phantoms ✅ confirmed   |
| cefi        | 0 phantoms / TBD real              | 1,290,707 phantoms 🔴 FALSE POS | Axis-10 (reconciler) | 0 phantoms ✅ confirmed   |
| defi        | 0 phantoms / 311,602 real          | 311,602 phantoms 🔴 FALSE POS   | Axis-10 (reconciler) | 0 phantoms ✅ confirmed   |

**Axis-10**: `ASSET_GROUP_CONFIG[ag]["prefix_tpls"]` in `reconcile_phantom_manifest_rows_all.py` only probed
pre-migration path shapes. Post-migration adds `pipeline_mode=batch_*/` before `asset_group=`. Fix adds
`pipeline_mode=batch_*/` template variants for cefi/defi/tradfi/prediction. Fix: `instruments-service@8accb30`
(2026-05-19).

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

**Source-of-truth rule**: every UAC `SOURCE_PRIORITY` entry MUST have a corresponding **batch** `PipelineMode` value,
and vice versa. Unit test in `unified-api-contracts/tests/unit/test_pipeline_mode.py` enforces the round-trip. (The
table above is illustrative, not exhaustive — UAC `PipelineMode` is the SSOT.)

## Source-aware modes + transport (M1/C-TRANSPORT, operator-ratified 2026-06-07)

The `pipeline_mode` axis is **source-aware for ALL three modes** — `batch_<source>`, `live_<source>`, and
`replay_<source>` — not batch-only. The canonical form is `{mode}_{source}[_{transport}]`:

- **`mode ∈ {batch, live, replay}`** — three CAPTURE modes of the SAME logical data / schema / paths:
  - `batch_<source>` — the T+1 floor (deep history).
  - `live_<source>` — a live-mode generator streamed to disk as it happens.
  - `replay_<source>` — an **intraday re-fetch** of a window `live` missed (cold-start / live-service down), same
    schema, tagged `replay` for the audit trail. Whether a `(source, data_type)` is replay-capable is a FACT in UAC
    `SOURCE_MODE_CAPABILITY` (M2) — a source that cannot re-fetch intraday simply means a live-downtime gap waits for
    batch (honest absence), not a decision.
- **`source` is the VENDOR only** — transport is NEVER glued into the source name (operator R4). The retired
  `hyperliquid_rest` source was that antipattern; it is now `source=hyperliquid` + `transport=rest`. `hyperliquid` is
  the one unified vendor that is BOTH a DeFi batch source (`batch_hyperliquid`, REST candleSnapshot) AND a CeFi/DeFi
  live+replay venue (`live_hyperliquid` / `replay_hyperliquid`).
- **`[_{transport}]`** — `transport ∈ {rest, websocket, flat_file}`. TWO rules:
  1. The transport SUFFIX appears in the `pipeline_mode` PATH KEY **only** where a source genuinely runs >1 transport
     for the SAME shard (else OMITTED — no noise). No source does today, so no member carries a suffix yet.
  2. A separate **`transport` manifest COLUMN is ALWAYS populated** on every captured row (UAC
     `default_transport_for_source(source)` unless the writer is passed an explicit value: `tardis` → `flat_file`, every
     other batch source → `rest`). The column is the always-populated SSOT; the suffix is path-pruning sugar.

**Read precedence is mode-contextual (M4)**: a live consumer reads `live > replay > batch`; a batch consumer reads
`batch > replay > live`; `replay` is always the middle (gap-fill) tier. (The object-side `live_websocket` →
`live_<source>` migration + the M4 reader are a separate GATED tranche; until then live still writes the transitional
`live_websocket` alias.)

## Reader behaviour

`UAC.SOURCE_PRIORITY` resolution at read time:

1. Stratify rows by `pipeline_mode` group (live vs each batch source).
2. Within each stratum, apply the existing `priority` ordering.
3. **Live always wins for dates where live exists**; batch wins where it doesn't.

This makes batch-vs-live reconciliation straightforward: pivot the same query by `pipeline_mode` and diff the per-shard
output. See `live_pipeline` Phase 12 for the full reconciliation gate criteria.

## Migration history

Bundled migration 2026-05-19 per
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

```yaml
execution:
  owner: data-pipeline maintainer (slot 3 Ikenna in active work-split, fallback owner: manifest-evolution maintainer)
  cadence: weekly check during the 30-day fallback window; daily for the final 7 days before deletion
  verifier: |
    `gcloud logging read 'jsonPayload.event="READER_FELL_BACK_TO_LEGACY_PATH"' --freshness=7d --limit=1` returns
    zero rows for 7 consecutive days BEFORE the fallback deletion cutoff. Reader-side parity verified via
    deployment-api `/api/data-status/shard-detail` smoke sample (5 asset_groups × 1 (venue, day) pair each).
  last_executed: NEVER (first execution gated on manifest v7→v8 cutover landing per
    `plans/active/manifest_schema_final_gate_2026_05_09.md` Phase 4)
```

(Added per codex audit D-20 2026-05-12 — Runbook Execution-Owner SSOT HARD RULE compliance.)

## Anti-patterns

- Don't keep the `category=` reader fallback long-term. Phase 8 of the migration plan deletes it 2026-06-15.
- Don't introduce a new batch `pipeline_mode` value without adding a corresponding `SOURCE_PRIORITY` entry. The
  round-trip unit test will fail.
- Don't glue a transport into the `source` (the `hyperliquid_rest` antipattern, retired R4 2026-06-07) — `source` is the
  VENDOR only; transport is the separate `transport` column (+ optional `[_{transport}]` suffix for a genuine
  > 1-transport source). See § "Source-aware modes + transport".
- `replay_<source>` is a REAL mode (intraday gap-fill), NOT a `live_websocket` write. (SUPERSEDES the prior "Don't use
  `pipeline_mode=replay_*`; replay writes to `live_websocket`" rule — that contradicted M1.) The object-side
  `live_websocket` → `live_<source>` + `replay_<source>` write migration is a separate GATED tranche.
- Don't write to manifest without the explicit `pipeline_mode=` kwarg post-migration. The default value is removed after
  Phase 4 sweep is grep-clean — explicit-or-fail. (UTL `add()` now AUTO-DERIVES it for a derivable market-data row —
  C-#2 — so a blank tag can't silently pass; features/service rows still keep `""`.)

## Cross-references

- Plan:
  [`gcs_migration_bundle_pipeline_mode_2026_05_08`](../../plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md)
- Foundation: [`availability-manifest-and-data-status.md`](./availability-manifest-and-data-status.md) — manifest
  schema + 4-state taxonomy + reason taxonomy.
- Sibling: [`../05-infrastructure/live-pipeline-architecture.md`](../05-infrastructure/live-pipeline-architecture.md) —
  consumer of the new partition for live-mode writes.
- Sibling: [`../05-infrastructure/replay-subsystem.md`](../05-infrastructure/replay-subsystem.md) — the replay subsystem
  (the source-aware `replay_<source>` write path lands in a separate gated tranche; see § "Source-aware modes +
  transport").
