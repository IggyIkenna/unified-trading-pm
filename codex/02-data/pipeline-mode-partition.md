---
doc_type: codex-ssot
title: "`pipeline_mode` Hive Partition"
summary: >-
  pipeline_mode hive-partition SSOT — the outermost {mode}_{source}[_{transport}] path key (LEFT of asset_group=) added
  to every parquet in the 2026-05-19 bundled GCS migration; the closed-set PipelineMode StrEnum round-tripped with
  SOURCE_PRIORITY, the source-aware live/replay M1-M8 ratified target design, the reader fallback chain, the
  GCS-delete-safety invariant (canonical-twin required), and the phantom-audit --apply prefix_tpls hazard.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    batch-live-reconciliation-service,
    deployment-api,
    features-service,
    instruments-service,
    market-tick-data-service,
    strategy-service,
  ]
scope: [engineer, admin]
tags: [pipeline-mode, manifest, migration, single-walk, canonicalisation, batch-live]
related:
  [
    /codex/02-data/pipeline-mode-and-batch-live-reconciliation.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/05-infrastructure/live-pipeline-architecture.md,
    /codex/05-infrastructure/replay-subsystem.md,
  ]
created: 2026-05-08
authoritative_for: [pipeline_mode hive-partition key, source-aware live/replay M1-M8 target design]
referenced_by:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/data-status-drilldown-hierarchy.md,
    /codex/02-data/data-status-drilldown.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/live-data-persistence-and-event-log.md,
    /codex/02-data/manifest-migration-coordination.md,
    /codex/02-data/pipeline-mode-and-batch-live-reconciliation.md,
  ]
owner:
last_reviewed: 2026-06-25
code_refs:
---

# `pipeline_mode` Hive Partition

> **STATUS** — Documents the `pipeline_mode` hive partition column added across every parquet on disk during the bundled
> GCS migration on 2026-05-19. Migration owner:
> [`plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md`](../../plans/archive/2026_05/gcs_migration_bundle_pipeline_mode_2026_05_08.md).
> If this doc disagrees with the active plan, the plan wins.
>
> **CANONICAL FORM (M1/C-TRANSPORT, operator-ratified 2026-06-07)**: `pipeline_mode = {mode}_{source}[_{transport}]`
> where `mode ∈ {batch, live, replay}`, `source` is the VENDOR only, and `[_{transport}]` is an OPTIONAL trailing
> segment present in the path key **only** where a source genuinely runs >1 transport for the SAME shard (else omitted).
> See § "Source-aware modes + transport" below — this SUPERSEDES the earlier batch-only `{batch_*, live_websocket}`
> framing (`live_websocket` is RETIRED; `live_<source>` is the current standard, and `replay_<source>` is a real mode).
> SSOT:
> [`plans/active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md`](../../plans/active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md).

## Shipped progress (updated 2026-05-19 post-Phase-3 run)

| Phase                                                       | Status                                                                                                                                             | Commit(s)                                                                       |
| ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| 0 — pre-audit doc (operator-runnable on same-region VM)     | ✅ shipped                                                                                                                                         | `unified-trading-pm@0cc633c8` (doc) + `@12483f5b` (plan flip)                   |
| 1A — UAC `PipelineMode` SSOT + closed-set round-trip        | ✅ shipped                                                                                                                                         | `unified-api-contracts@8bc3f2a`                                                 |
| 1B — UTL `ManifestWriter` `pipeline_mode` kwarg + tests     | ✅ shipped                                                                                                                                         | `unified-trading-library@87134364`                                              |
| 1C — UAC `SOURCE_PRIORITY` `pipeline_mode` field            | ✅ shipped                                                                                                                                         | `unified-api-contracts@6a8529f` + `unified-trading-pm@53c498c5`                 |
| 2 — Canonical migration script + 23 unit tests              | ✅ shipped                                                                                                                                         | `unified-trading-pm@5a3c360a` + `@cc6fe4ce` (plan flip)                         |
| 3 — VM fleet execution (31 VMs, all 5 asset_groups)         | ✅ complete                                                                                                                                        | 2026-05-19 13:52→16:01 UTC; all 31 VMs TERMINATED exit 0. No data loss.         |
| 4 — Workspace-wide consumer sweep                           | ✅ complete                                                                                                                                        | All production callsites pass explicit `pipeline_mode=`. No gaps found.         |
| 5.1 — UTL `read_manifest_with_source_priority` reader       | ✅ shipped                                                                                                                                         | `unified-trading-library@52f123d6` + `unified-trading-pm@2a0d105d` (annotation) |
| 5.2 — MTDS/MDPS path probers                                | ✅ shipped                                                                                                                                         | `market-tick-data-service@33b2ae5` (2026-05-19)                                 |
| 5.3 — Sports/DeFi `candidate_parquet_paths` extension       | ✅ shipped                                                                                                                                         | `unified-api-contracts@fefd720` (2026-05-19)                                    |
| Axis-10 — Reconciler pipeline_mode= prefix fix              | ✅ shipped                                                                                                                                         | `instruments-service@8accb30` (2026-05-19) — see pre/post counts below          |
| 3.6 — Post-migration phantom gate (re-audit w/ Axis-10 fix) | ✅ complete                                                                                                                                        | prediction ✅ 0 / sports ✅ 0 / tradfi ✅ 0 / defi ✅ 0 / cefi ✅ 0             |
| 6 — Residual phantom cleanup                                | 🚫 not needed                                                                                                                                      | Axis-10 false positives; parquets exist at new paths. DO NOT run `--apply`.     |
| 8 — Reader fallback removal (T+30d, ~2026-06-15)            | ⏸ deferred, now significantly overdue (verified 2026-08-12: `unified_trading_library/manifest_reader_fallback.py` levels 1/3/4 still live in code) | "no double SSOT" rule once `READER_FELL_BACK_TO_LEGACY_PATH` count = 0 / 7d.    |
| 9 — Final workspace-wide QG sweep                           | ⏳ pending                                                                                                                                         | Sequential after Phase 3.6 operator sign-off.                                   |

> **🔴 GCS DELETE SAFETY INVARIANT (codified 2026-06-18; HARD RULE).** The v9 migration COPIED objects to canonical
> `pipeline_mode={mode}_{source}/asset_group={ag}/…` paths (COPY not MOVE) → the legacy bare `asset_group=`/`category=`/
> top-level `day=` shapes are DUPLICATES that still exist. The `_index` is CELL-KEYED (path-agnostic), so it does not by
> itself tell you a cell's data is canonical. **NEVER delete a legacy object without `gcs_describe_object`-verifying a
> twin already in CANONICAL format** (defi: + normalized venue/itype). A reconcile prefix-matches BOTH shapes, so it
> only proves "some object exists" — a cell backed ONLY by a legacy copy passes reconcile yet would be ORPHANED by a
> blind delete AND read MISSING under canonical-only data-status (deployment-api `DATA_STATUS_CANONICAL_PATHS_ONLY`).
> Two buckets per legacy object: **SAFE-TO-DELETE** (canonical twin verified) vs **MIGRATE-FIRST** (no twin → COPY to
> canonical first via `migrate_*_v9_canonical`, then delete-safe). Require **100% canonical-twin coverage per AG**
> before executing that AG's delete-list; deletion is OPERATOR-GATED. SSOT:
> `plans/active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md` § "GCS delete safety — path/schema
> migration prerequisite map" (moved 2026-07-26 — was
> `plans/active/instruments_mtds_subset_consistency_remediation_2026_06_17.md` before its 2026-07-24 3-way line-cap
> split + 2026-07-26 archival) + `plans/audit/results/gcs_delete_list_and_e2e_data_accounting_2026_06_18.md`.

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

**Why `--apply` is dangerous on false-positive phantom counts (HARD RULE)**: `--apply` reconciles manifest rows against
GCS by flipping any row whose parquet cannot be found at the probed prefix to `attempted_failed`. When the prefix
templates are stale (i.e. the Axis-10 class of bug — templates still pointing at pre-migration path shapes), the
reconciler CANNOT find the canonical-path objects it should be finding, producing large false-positive phantom counts.
Running `--apply` in that state **flips real `captured` rows → `attempted_failed`**, silently corrupting the manifest's
honest-coverage accounting. Always verify `ASSET_GROUP_CONFIG[ag]["prefix_tpls"]` covers the new path shape with a
`--dry-run` first; fix any missing `pipeline_mode=<mode>_*/` template variants; re-run `--dry-run` until the phantom
count drops to zero; THEN run `--apply`. The Phase 6 "DO NOT run `--apply`" in the table above reflects this: those
phantom counts were false positives from stale templates, and `--apply` there would have corrupted real `captured` cells
for all five asset groups.

## TL;DR

`pipeline_mode` is the outermost hive partition column added to every parquet path:

```
gs://{pid}-raw-tick/raw_tick_data/by_date/day=YYYY-MM-DD/pipeline_mode=live_binance/asset_group=cefi/venue=binance/...
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

| Value                         | Source                                                                                                                                                                                                                                                             |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `batch_databento`             | Databento bulk + replay APIs (CME GLBX.MDP3 trades, OHLCV)                                                                                                                                                                                                         |
| `batch_tardis`                | Tardis CeFi historical ticks                                                                                                                                                                                                                                       |
| `batch_ccxt`                  | CCXT REST batch (per-instrument T+1 reconcile)                                                                                                                                                                                                                     |
| `batch_barchart`              | RETIRED 2026-06-24; Barchart removed as a source. VIX 15m now aggregates from VX futures via Databento (XCBF.PITCH → `batch_databento`) with `batch_yahoo` for the rolling window. No shim.                                                                        |
| `batch_yahoo`                 | VIX 15m rolling window (last 60d) + tradfi ETFs                                                                                                                                                                                                                    |
| `batch_api_football`          | api_football fixtures / events / lineups / stats                                                                                                                                                                                                                   |
| `batch_footystats`            | footystats odds / xG                                                                                                                                                                                                                                               |
| `batch_understat`             | understat xG / shot maps                                                                                                                                                                                                                                           |
| `batch_transfermarkt`         | transfermarkt player values                                                                                                                                                                                                                                        |
| `batch_soccer_football_info`  | SFI progressive stats                                                                                                                                                                                                                                              |
| `batch_open_meteo`            | open-meteo weather (per fixture)                                                                                                                                                                                                                                   |
| `batch_odds_api`              | odds_api closing-line + horizon snapshots                                                                                                                                                                                                                          |
| `batch_polymarket_historical` | Polymarket CLOB historical                                                                                                                                                                                                                                         |
| `batch_kalshi_historical`     | Kalshi historical                                                                                                                                                                                                                                                  |
| `batch_lighter_candles`       | Lighter `/candles` historical (per dex_perp_onboarding 2026-05-07)                                                                                                                                                                                                 |
| `batch_pacifica_kline`        | Pacifica `/kline` historical                                                                                                                                                                                                                                       |
| `batch_databento_replay`      | Databento used by the replay-cascade subsystem                                                                                                                                                                                                                     |
| `live_<source>`               | Live streaming pipeline (MTDS / MDPS / features-service live mode). Formerly the transitional `live_websocket` alias (RETIRED — M1-BREAKING tranche complete 2026-06-30; fleet-wide 0 `.py` hits; cefi manifest: 15,993 `live_<source>` rows, 0 `live_websocket`). |

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
`live_<source>` migration is COMPLETE — M1-BREAKING tranche shipped; `live_websocket` is RETIRED.)

## Ratified TARGET design — live/replay (M1–M8 settled contract)

> **This section is the SETTLED codex contract** for the batch/live/replay final-target design (operator-ratified
> 2026-06-05, all 6 decisions; R4 transport rule 2026-06-07; codified here per M-COORD-1/R6-codex 2026-06-11). Plans
> REFERENCE this section — not vice versa. Design provenance:
> [`plans/active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md`](../../plans/active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md)
> (M1–M9). Items marked **[GATED — `M1-BREAKING` tranche]** are the ratified target whose OBJECT/code migration has not
> yet run; everything else is live contract today.

### M1 — object layout: `live_<source>` / `replay_<source>` **[LANDED — `M1-BREAKING` tranche COMPLETE 2026-06-30]**

Live and replay objects land on the SAME canonical hive path as batch, differing only in the `pipeline_mode=` value
(LEFT of `asset_group=`, byte-identical otherwise — batch=live):

```
…/raw_tick_data/by_date/day=YYYY-MM-DD/pipeline_mode=batch_databento/asset_group=tradfi/venue=…   (T+1 floor)
…/raw_tick_data/by_date/day=YYYY-MM-DD/pipeline_mode=live_databento/asset_group=tradfi/venue=…    (streamed live)
…/raw_tick_data/by_date/day=YYYY-MM-DD/pipeline_mode=replay_databento/asset_group=tradfi/venue=…  (intraday gap-fill)
```

The source-aware live value fixes the live multi-source PATH COLLISION (two live sources for one cell both writing
`pipeline_mode=live_websocket/…` → same path → silent overwrite). The `M1-BREAKING` tranche is COMPLETE (2026-06-30):
live writers emit `live_<source>`; `replay_<source>` writers are live; the transitional `live_websocket` alias is
RETIRED (0 fleet-wide `.py` hits; cefi manifest: 15,993 `live_<source>` rows, 0 `live_websocket`). Readers PREFIX-match
`batch_*` / `live_*` / `replay_*` (+ bare legacy) — never an exact coarse literal.

### M2×M3 — capability + per-shard availability registries (UAC SSOT)

- **M2 — `SOURCE_MODE_CAPABILITY`** (UAC `canonical/crosscutting/source_priority.py`): per `source`, the frozen set of
  modes it CAN run `{BATCH, LIVE, REPLAY}`. **Replay (crisp definition)** = the source can retrieve a RECENT window ON
  DEMAND — "today's data from start-of-day" — to fill an intraday / startup / live-downtime gap (format-agnostic). Chain
  RPCs are always replay-capable (deterministic); an end-of-day-archive vendor is NOT (`tardis` = batch-only; CeFi
  live/replay sources are the EXCHANGES themselves). The data-type-aware lookup is per-`(source, data_type)` —
  **`modes_for(source, data_type)` (LANDED — M2-REFINEMENT, unified-api-contracts@a56a7fc2)** derived from the
  per-operation `SourceCapability.operations` split (a `ws_<data_type>` op ⇒ `LIVE`, REST op ⇒ `BATCH`; `REPLAY` is the
  live-gap-fill tier, so it drops WITH live) — refining the coarse per-source `modes_for_source` ONLY for live sources
  that use the ws/REST convention (the CeFi venues + hyperliquid); every other source returns the coarse set unchanged.
  E.g. hyperliquid is `{BATCH, LIVE, REPLAY}` for `trades`/`l2_book` but `{BATCH}` for `funding_rates` (REST-only — no
  ws op). Keep `modes_for_source` for source-level questions (the capability matrix, the replay-capable set).
- **M3 — per-shard available-sources registry**: per shard atom, which sources serve it. **M2 × M3 →
  `could_exist(shard, mode)`** — the guardrail that the could-exist denominator, the data-status views, and the startup
  gate all read; never look for (or count against coverage) data that cannot exist for that shard in that mode. Extends
  the instrument-existence guard + could-exist denominator to the mode axis.

### M4 — mode-contextual read precedence (`select_for_mode`)

Precedence is a CONSUMER config, not one global order: a **live-mode consumer** reads `live > replay > batch`; a
**batch-mode consumer** (backtest / T+1 reconciliation) reads `batch > replay > live`. `replay` is ALWAYS the middle
(gap-fill) tier. The data-status surface is mode-AGNOSTIC (M5 union: ≥1 mode `captured` ⇒ cell `captured`; M4 only picks
the representative row — shipped `deployment-api@4dd2575`/`@46e3d57`). The live read-path resolver
`select_for_mode(consumer_mode, available_modes)` lives in **batch-live-reconciliation-service** — **[LANDED]**, not
gated (corrected 2026-08-09: M1-BREAKING shipped 2026-06-30 and M4 itself was independently verified shipped 2026-07-12;
the stale `[GATED — rides M1-BREAKING]` tag outlived both).

### M6 — capability-driven startup gate (the `[batch-cutoff → now]` tail)

Feature lookback (e.g. a 100-day MA) is satisfied by **batch**; the real continuity risk at a live flip is the
`[batch-cutoff → now]` tail. The fill policy is a static per-shard fact read from M2×M3 — the code KNOWS which applies:

1. shard has a **replay-capable** source → autostart `replay_<source>` over `[cutoff → now]` (autonomous);
2. no replay but a **live** source → live must ALREADY be running (started ahead) — else the shard cannot operate;
3. no replay AND no live (batch sole SSOT — e.g. sports fixtures) → wait for batch / refuse to start / a
   configured-OK-gap (per-shard DR config).

Homes: batch-live-reconciliation-service + strategy-service (live-flip readiness gate) + MTDS (startup). **[GATED]**

### M7 — autonomous replay recovery

Alerting + auto-recovery DETECT a gap (batch stopped + no live + replay-capable shard) and FIRE `replay_<source>`
themselves — same-data where capable, autonomously. "Gaps are OK" is a per-shard DR config, never a default. Composes
with [`/codex/04-architecture/autonomous-recovery-matrix.md`](/codex/04-architecture/autonomous-recovery-matrix.md).
**[GATED]**

### M8 — cadence is a COLUMN (an observability axis), NEVER a path key

`pipeline_mode` (batch/live/replay × source) is the **reconciliation/provenance axis** the reader unions over.
Operational cadence / deployment topology is a SEPARATE axis:
`Cadence ∈ {one_off_backfill, t1_daily, scheduled_recurring, continuous_live, recovery_replay}` (UAC enum, shipped) —
carried as a **manifest COLUMN + the deployment-registry `run_class`**, NOT a GCS path key, so it never fragments the
data or the union. A T+1 daily Tardis pull and a one-off historical Tardis backfill are BOTH `batch_tardis` (ONE
pipeline to union) differing only in cadence. Reference data (IS instruments/fixtures, api-football 7-days-ahead
fixtures) is `batch_<source>` + cadence `scheduled_recurring` — sparse/forward-looking is a cadence property, not a new
pipeline_mode. The `transport` column (shipped, § above) is the wiring model the cadence column follows. **[column
wiring GATED — rides the v9 walk per M5b single-walk discipline]**

### T+1 batch≈live reconciliation + live TTL **[GATED — after M4 + `M1-BREAKING` live writers]**

Once batch lands for a window, the batch-live-reconciliation-service confirms **batch ≈ live within a tolerance**, then
a TTL clears the now-redundant `live_<source>` cells (batch is the durable SSOT). Long-lived `replay_<source>` stays
where batch never existed. Config knobs (sensible defaults): reconciliation tolerance + TTL horizon. Repo:
batch-live-reconciliation-service (+ UTL TTL helper). Agreement-rule details:
[`pipeline-mode-and-batch-live-reconciliation.md`](pipeline-mode-and-batch-live-reconciliation.md).

## Reader behaviour

`UAC.SOURCE_PRIORITY` resolution at read time:

1. Stratify rows by `pipeline_mode` group (live / replay / each batch source).
2. Within each stratum, apply the existing `priority` ordering.
3. Across strata, apply the **M4 mode-contextual precedence** (§ "Ratified TARGET design" above): a live consumer reads
   `live > replay > batch`; a batch consumer reads `batch > replay > live`. (The legacy single-context "live always
   wins" rule at `source_priority.py:628` is the live-consumer special case — the full `select_for_mode` resolver is the
   M4 item (LANDED, see § M4 above).)

This makes batch-vs-live reconciliation straightforward: pivot the same query by `pipeline_mode` and diff the per-shard
output. See `live_pipeline` Phase 12 for the full reconciliation gate criteria.

## Migration history

Bundled migration 2026-05-19 per
[`gcs_migration_bundle_pipeline_mode_2026_05_08`](../../plans/archive/2026_05/gcs_migration_bundle_pipeline_mode_2026_05_08.md).
Three migrations rode together:

1. Add `pipeline_mode=` segment to every existing batch parquet, applying the source-priority entry's value (e.g.
   `batch_databento` for Databento-written parquets, `batch_tardis` for Tardis).
2. Finish the `category=` → `asset_group=` rekey CLAUDE.md previously preserved as legacy-with-fallback.
3. Sweep up the 5 drift axes from the 2026-05-04 phantom-audit incident (path-prefix, instrument_type casing, schema-4
   empty instrument_type, chain-bundle equivalence, etc.).

The manifest was rewritten ONCE during the bundle — readers continue to function via the fallback chain (see below).

## Reader fallback chain (≤30 days post-migration; scheduled deletion 2026-06-15 — NOT executed, see correction below)

UTL `read_manifest_with_source_priority(...)` + MTDS / MDPS path probers + sports `candidate_parquet_paths` helper try
canonical path first, then fall back through:

1. Without `pipeline_mode=` segment (pre-migration shape).
2. With legacy `category=` instead of `asset_group=`.
3. With legacy `day=*/` prefix instead of `raw_tick_data/by_date/day=*/`.
4. Combinations of the above.

Each fallback hit emits a `READER_FELL_BACK_TO_LEGACY_PATH` event so we can monitor when fallbacks are no longer needed.
Fallback paths were **scheduled for deletion T+30 days post-migration** per workspace "no double SSOT" rule, tracked in
the migration plan's Phase 8. **Correction 2026-08-12 (docs-drift fix)**: that deletion never actually happened — no
newer operator ruling supersedes the deferral either; this section previously read "(deleted 2026-06-15)" in past tense,
which was wrong. Live-code check (`unified-trading-library/unified_trading_library/manifest_reader_fallback.py`,
2026-08-12) confirms all 5 fallback levels are still present and exercised. Per that module's own docstring, level 2
(`category=` legacy hive vocab) is a **permanent, documented exception** to the "no double SSOT" rule (asset-group
vocabulary preserved on disk, not scheduled for removal) — only levels 1/3/4 (strip-`pipeline_mode` / legacy
`day=`-prefix variants) are the transitional ones Phase 8 was meant to delete once `READER_FELL_BACK_TO_LEGACY_PATH`
drops to zero for 7 consecutive days. That verification was never run (see the migration plan's own Phase 8 status).
Phase 8 stays open/overdue, not silently abandoned — a real remaining-work item, not a stale doc claim.

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

- Don't keep the transitional (levels 1/3/4: strip-`pipeline_mode` / legacy `day=`-prefix) reader fallback levels
  long-term — Phase 8 of the migration plan was meant to delete them 2026-06-15 but never ran (still open/overdue as of
  2026-08-12, see § "Reader fallback chain" above). **Correction 2026-08-12**: this line previously named the
  `category=` fallback (level 2) as the one to delete — that was backwards; `category=` is the one PERMANENT, documented
  exception (asset-group vocabulary preserved on disk, per CLAUDE.md), not scheduled for removal.
- Don't introduce a new batch `pipeline_mode` value without adding a corresponding `SOURCE_PRIORITY` entry. The
  round-trip unit test will fail.
- Don't glue a transport into the `source` (the `hyperliquid_rest` antipattern, retired R4 2026-06-07) — `source` is the
  VENDOR only; transport is the separate `transport` column (+ optional `[_{transport}]` suffix for a genuine
  > 1-transport source). See § "Source-aware modes + transport".
- `replay_<source>` is a REAL mode (intraday gap-fill), NOT a `live_websocket` write. (SUPERSEDES the prior "Don't use
  `pipeline_mode=replay_*`; replay writes to `live_websocket`" rule — that contradicted M1.) The object-side
  `live_websocket` → `live_<source>` + `replay_<source>` write migration is COMPLETE (M1-BREAKING tranche landed
  2026-06-30; `live_websocket` RETIRED).
- Don't write to manifest without the explicit `pipeline_mode=` kwarg post-migration. The default value is removed after
  Phase 4 sweep is grep-clean — explicit-or-fail. (UTL `add()` now AUTO-DERIVES it for a derivable market-data row —
  C-#2 — so a blank tag can't silently pass; features/service rows still keep `""`.)

## Cross-references

- Plan:
  [`gcs_migration_bundle_pipeline_mode_2026_05_08`](../../plans/archive/2026_05/gcs_migration_bundle_pipeline_mode_2026_05_08.md)
- Foundation: [`availability-manifest-and-data-status.md`](./availability-manifest-and-data-status.md) — manifest
  schema + 4-state taxonomy + reason taxonomy.
- Sibling:
  [`/codex/05-infrastructure/live-pipeline-architecture.md`](/codex/05-infrastructure/live-pipeline-architecture.md) —
  consumer of the new partition for live-mode writes.
- Sibling: [`/codex/05-infrastructure/replay-subsystem.md`](/codex/05-infrastructure/replay-subsystem.md) — the replay
  subsystem (the source-aware `replay_<source>` write path lands in a separate gated tranche; see § "Source-aware
  modes + transport").
