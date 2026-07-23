---
doc_type: plan
title: Data-status multi-axis shard propagation (display + manifest axis correctness)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    deployment-ui,
    execution-service,
    instruments-service,
    market-data-processing-service,
  ]
scope: [engineer, admin]
tags: []
related:
  [
    shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md,
    /plans/archive/2026_05/writegate_honest_coverage_endtoend_2026_05_06.md,
    data_status_offline_rollup_2026_05_06.md,
    feature_dag_uac_ssot_and_features_coverage_2026_05_06.md,
    data_status_operations_dropdown_cli_derived_2026_05_07.md,
  ]
created: "2026-05-06"
locked_by: live-defi-rollout
locked_since: 2026-05-06
---

# Data-status multi-axis shard propagation

## Why

The CLAUDE.md per-asset-group shard-key matrix declares each asset_group's shard atom as a multi-axis tuple (DeFi keys
on `chain`, Sports on `league_id`, Prediction on `canonical_question_group`, ML on `model_family + training_period`,
etc.). The **writers** (orchestrator, ManifestWriter callsites) are being brought into compliance under the companion
`shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md`.

This plan addresses the **read/display side** — the gap between what shards the manifest captures and what the
data-status panel reveals to the user.

### When to shard vs when to just add a display axis (axis SSOT)

This plan distinguishes two related-but-different ideas. Conflating them inflates the manifest and the work for no
benefit.

A column belongs in the **shard atom** (one manifest row per unique value) ONLY when at least one of these holds:

1. **Failure isolation** — a write of one value can fail independently of others. Wrong example:
   instruments-service-DEFI fetches all reserves for an AaveV3 chain in one subgraph call and writes one parquet;
   sharding per-instrument-type buys nothing because there is one I/O. Right example: MTDS CeFi spot per-instrument
   writes (each instrument's tick stream is a separate fetch).
2. **Memory ceiling** — the chunk would exceed practical RAM as a single write. MTDS per-instrument tick parquet (35 GB+
   per venue per day) is the canonical case. Instruments-service per-venue rows are KB-scale; no memory pressure.
3. **Concurrency orthogonality** — independent shards can run on different workers/VMs because their I/O does not
   overlap. TARDIS exception: it downloads the whole exchange's deltas once and then splits across days for parquet
   writes — day-sharding here is "necessary evil" for the per-day file layout, not for fetch parallelism.

If none of (1)/(2)/(3) applies, the column is a **display axis only**: populate it on each row for filtering/grouping in
the UI, but DO NOT introduce one row per value. Examples for instruments-service:

- instrument_type (SPOT/PERP/OPT/FUT) is a Databento/TARDIS-bulk attribute not a shard atom — kept as a row column for
  filter/group, not a key.
- For DeFi, `chain` IS in the shard atom because each chain is a separate RPC/subgraph fetch with independent failure
  modes (chain-RPC outages happen in isolation). It is not display-only.

Day is implicit on every row — batch mode dumps per-day parquets, live mode runs continuously but the manifest grain is
`(other-axes, day)`. So "per-day" doesn't appear separately in the matrix below; it is on every row.

Currently `/api/data-status/coverage-summary` only emits one breakdown axis per asset_group (venue, or data_type for
sports). `/api/data-status/manifest` (the cell-grid endpoint) only slices on `venue × data_type × date`. Both silently
aggregate over `chain`, `instrument_type`, `league_id`, `canonical_question_group`, `feature_group`, `timeframe`,
`model_family`, `strategy_id`, `instruction_type`, `job_id`. A user looking at the DEFI grid can't tell whether ETHEREUM
caught up but SOLANA dragged; a user looking at SPORTS can't see the per-fixture or per-league breakdown; an ML/strategy
operator can't see which experiment configs ran successfully.

## Scope (the gap to close)

Three classes of fix needed. All three apply per-service per-asset_group with different axis sets:

1. **Manifest schema additions** — columns the writer needs to populate but the v5 schema doesn't yet have (`fixture_id`
   for sports, `job_id` for ML/strategy/execution).
2. **Per-service axis SSOT** — declarative table of which axes apply to which `(service, asset_group)` pair, lifted into
   UAC.
3. **Endpoint + UI consumption** — `/coverage-summary` emits per-axis breakdowns; `/manifest` cell-grid supports
   secondary-axis slicing; the deployment-ui DataStatusTab renders both.

## Per-service axis matrix (corrected after 2026-05-06 audit)

Two columns per asset_group:

- **Shard axes** (one manifest row per unique tuple of values) — earns its place by failure-isolation, memory, or
  concurrency. Day is implicit on every row.
- **Display axes** (kept as row attributes for UI filter/group; NOT shard atoms) — useful for breakdowns without
  inflating the manifest.

🚫 = service does not cover this asset_group.

| Service                                                                 | Asset group                         | Shard axes (key)                                                                                                                                                       | Display axes (filter/group only) |
| ----------------------------------------------------------------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| **instruments-service** _(bulk-fetched per venue, written flat)_        | CEFI                                | venue                                                                                                                                                                  | instrument_type, data_type       |
|                                                                         | TRADFI                              | venue                                                                                                                                                                  | instrument_type, data_type       |
|                                                                         | DEFI                                | venue, **chain**                                                                                                                                                       | instrument_type, data_type       |
|                                                                         | SPORTS                              | data*type, **league_id** *(plenty of fixtures per league per day; we render the per-fixture list at drill-down time from the parquet itself, not from the manifest)\_  | source                           |
|                                                                         | PREDICTION                          | venue, **canonical_question_group** _(today encoded as `data_type` — `BTC`/`ETH`/`SPX`; UAC follow-up plan resolves)_                                                  | data_type                        |
| **market-tick-data-service**                                            | CEFI                                | venue, **instrument_id** (or _bundle root_ for `options_chain` / `futures_chain`), data_type                                                                           | instrument_type                  |
|                                                                         | TRADFI                              | venue, **instrument_id** or bundle root, data_type                                                                                                                     | instrument_type                  |
|                                                                         | DEFI                                | venue (= protocol), **chain**, instrument_id or protocol_id, data_type                                                                                                 | instrument_type                  |
|                                                                         | SPORTS                              | data*type, **league_id** *(per-fixture from parquet at drill-down, not manifest)\_                                                                                     | source                           |
|                                                                         | PREDICTION                          | venue, **canonical_question_group**, data_type                                                                                                                         | —                                |
| **market-data-processing-service**                                      | (same axes as MTDS per asset_group) |                                                                                                                                                                        |                                  |
| **features-delta-one-service**                                          | CEFI / TRADFI                       | venue, **feature_group**, **timeframe**, instrument_id (where the calculator is per-instrument)                                                                        | instrument_type                  |
|                                                                         | DEFI                                | venue, **chain**, feature_group, timeframe, instrument_id-or-protocol-id                                                                                               | instrument_type                  |
|                                                                         | SPORTS / PREDICTION                 | 🚫                                                                                                                                                                     |                                  |
| **features-volatility-service**                                         | (same shape as delta-one)           |                                                                                                                                                                        |                                  |
| **features-onchain-service**                                            | DEFI only                           | venue, **chain**, **feature_group** (sourced upstream — `lending_rates`, `lst_yields`, `gas_fees`, `dex_liquidity`, `bridge_events`, etc.), protocol_id, timeframe     | —                                |
|                                                                         | other asset_groups                  | 🚫                                                                                                                                                                     |                                  |
| **features-sports-service**                                             | SPORTS only                         | **feature_group** (upstream-source-keyed — `api_football_only`, `footystats_only`, `understat_only`, `sfi_progressive_only`, `cross_source`, `weather`), **league_id** | source, data_type                |
|                                                                         | other asset_groups                  | 🚫                                                                                                                                                                     |                                  |
| **features-calendar-service**                                           | SHARED (cross-asset)                | **feature_group** (source-keyed — `fred`, `tradingeconomics`, `sec`, `holiday_calendar`), timeframe                                                                    | —                                |
| **features-cross-instrument-service**                                   | per asset_group                     | venue, **feature_group**, **timeframe**                                                                                                                                | instrument_type                  |
|                                                                         | DEFI                                | + **chain**                                                                                                                                                            |                                  |
|                                                                         | PREDICTION                          | venue, **canonical_question_group**, feature_group, timeframe                                                                                                          | —                                |
| **features-multi-timeframe-service**                                    | per asset_group                     | venue, **timeframe**, **feature_group**                                                                                                                                | instrument_type                  |
|                                                                         | DEFI                                | + **chain**                                                                                                                                                            |                                  |
| **features-commodity-service**                                          | TRADFI only                         | venue, **feature_group**                                                                                                                                               | instrument_type                  |
| **ml-training-service** _(experiment-based; pools across asset_groups)_ | SHARED                              | **model_family**, **training_period**, **job_id** 🆕                                                                                                                   | client_id, asset_group           |
| **ml-inference-service** _(experiment-based)_                           | SHARED                              | **model_family**, **job_id** 🆕                                                                                                                                        | client_id, asset_group           |
| **strategy-service** _(per-asset-group + experiment-keyed)_             | per asset_group                     | **strategy_id**, **job_id** 🆕                                                                                                                                         | archetype, client_id             |
| **execution-service** _(per-asset-group + experiment-keyed)_            | per asset_group                     | **strategy_id**, **instruction_type**, **job_id** 🆕                                                                                                                   | venue, client_id                 |

**Shard-axis decisions justified:**

- **instruments-service**: instrument_type is **NOT** a shard atom. Databento (TradFi) fetches all instruments for a
  venue in bulk; TARDIS (CeFi) does the same per exchange. Sharding by instrument_type would mean 20× the same fetch +
  filter — pure waste. Keep instrument_type as a row column for the breakdown view, not as a key.
- **MTDS**: per-instrument is a real shard because each instrument is a separate fetch and the resulting tick parquet is
  GB-scale (memory). Bundle-root sharding (`options_chain` / `futures_chain`) groups symbols that share a chain feed.
- **DeFi `chain`** IS a shard axis because each chain is a separate RPC / subgraph endpoint with independent failure
  modes.
- **Sports `fixture_id`** is **NOT** a shard atom. `(league_id, day)` already bounds fixtures to a small set (typically
  <20 in a top league). The drill-down view reads the fixture list from the parquet itself; no per-fixture manifest row
  needed. Keeps the sports manifest compact.
- **Experiment-based services** shard on `job_id` so an operator can watch one experiment's progress without it being
  mixed with other concurrent runs. Re-running the same configs = a new `job_id`, **not** idempotent skip (we want
  versioned/auditable history of every run).

## What this changes vs current state

### Manifest schema (v6 → v7 additions, additive only)

Audit 2026-05-06: instruments-service, MTDS, features-onchain are mostly on schema_version=6. Older v4/v5 rows survive
in the manifest from before the v5→v6 migration (which added `quote_asset`, `margin_type`, `combo_type`, `leg_weights`).
Adding `job_id` is the same pattern — a v6→v7 additive bump. Readers tolerate older rows missing the new column (null
fallback).

- Add **`job_id`** column (string, nullable). ML/strategy/execution writers populate it with the unique experiment-run
  identifier (sortable timestamp tag like `RUN_TS-${experiment_name}` or UUID). All other services leave null. Job-id
  semantics: **Option 1** — every experiment configuration bundle gets a unique `job_id` at launch; configs route to
  shards under that `job_id`; completion tracked per-job (we wait for all configs to finish under that job_id). Same
  configs re-run = a new `job_id`, NOT idempotent skip — preserves the audit trail of every experiment version.

`fixture_id` was considered and dropped from this plan: `(league_id, day)` sharding already bounds the fixture set to a
small per-day count; per-fixture detail comes from the parquet itself at drill-down time, not from a separate manifest
row. Avoids an unnecessary schema column + manifest expansion.

`client_id` already exists in v6. Continuing to use it alongside `job_id` for multi-tenant scoping (which client
triggered an inference / strategy run); `job_id` is the experiment-run identifier within that client's scope. Both are
populated when applicable.

### Per-(service, asset_group) axis matrix → UAC SSOT

New module `unified_api_contracts/registry/data_status_axis_matrix.py`:

```python
SHARD_AXIS_MATRIX: dict[tuple[str, str], tuple[str, ...]] = {
    ("instruments-service", "CEFI"): ("venue",),
    ("instruments-service", "DEFI"): ("venue", "chain"),
    ("instruments-service", "SPORTS"): ("data_type", "league_id"),
    ("instruments-service", "PREDICTION"): ("venue", "canonical_question_group"),
    ("market-tick-data-service", "CEFI"): ("venue", "instrument_type", "instrument_id", "data_type"),
    ("market-tick-data-service", "DEFI"): ("venue", "chain", "instrument_type", "instrument_id", "data_type"),
    ("market-tick-data-service", "SPORTS"): ("data_type", "league_id", "fixture_id"),
    ...
}

PRIMARY_AXIS: dict[tuple[str, str], str] = {
    # The single axis the cell-grid uses for its main dimension. Other axes
    # in SHARD_AXIS_MATRIX become secondary breakdowns / drill-downs.
    ("instruments-service", "DEFI"): "venue",
    ("market-tick-data-service", "DEFI"): "venue",
    ("ml-training-service", "*"): "model_family",
    ...
}
```

Every per-service writer + every endpoint reads from this single SSOT.

### `/coverage-summary` response shape (additive, backward-compat)

```json
"DEFI": {
  "latest_day": "2026-05-03",
  "latest_day_total": 4922,
  "latest_day_instruments": {"BALANCER": 2180, "UNISWAP_V3": 1742, ...}, // kept for backward-compat
  "breakdowns": {
    "venue": {"BALANCER": 2180, "UNISWAP_V3": 1742, ...},
    "chain": {"ETHEREUM": 3402, "ARBITRUM": 612, "SOLANA": 488, ...},
    "instrument_type": {"LENDING_POOL": 1240, "DEX_POOL": 3500, ...},
    "data_type": {...}
  }
}
```

### `/manifest` cell-grid response shape (additive query-param)

New optional query params:

- `?secondary_axis=chain` — slices the cell grid by venue × chain × data_type × date
- `?league_id=PREMIER_LEAGUE` — filters sports cells to one league
- `?canonical_question_group=BTC_HOURLY` — filters prediction cells to one group
- `?job_id=RUN-2026-05-06-abc` — filters strategy/execution cells to one run

Backward-compat: omitted params → today's behaviour.

### deployment-ui DataStatusTab changes

- DEFI tab: chain dropdown selector (top-of-panel), default = "all chains".
- SPORTS tab: league + fixture drill-down (already partially there per `data_status_drilldown_followups_PROMPT.md`).
- Strategy/Execution tab: job_id selector + "show last N runs" toggle.
- ML training tab: model_family selector + training_period dimension.
- Generic: a `breakdowns` accordion showing per-axis counts under each asset_group card.

## Pre-audit blast radius

### Manifest schema columns (UTL ManifestWriter + readers)

- `unified_trading_library/manifests/manifest_writer.py` — add `fixture_id`
  - `job_id` to the canonical column list.
- `unified_trading_library/manifests/manifest_reader.py` — same.
- All consumer services that read the manifest (instruments-service, MTDS, MDPS, features-\*, deployment-api). Most
  should pick up the new columns transparently because pandas concat tolerates new columns.

### Writers (per-service)

| Service              | What needs to populate `job_id` |
| -------------------- | ------------------------------- |
| ml-training-service  | every shard write               |
| ml-inference-service | every shard write               |
| strategy-service     | every backtest shard write      |
| execution-service    | every backtest shard write      |
| (all other services) | n/a — leave null                |

For per-(service, asset_group) writers, also confirm the **shard axes** column populates correctly (already-existing
columns):

| Service / asset_group            | Confirm written                                                                                                                                      |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| instruments-service / DEFI       | `chain` — already done in this session via orchestrator `_write_venue` fix + 64,060-row migration                                                    |
| instruments-service / PREDICTION | `canonical_question_group` (today encoded in `data_type`); successor plan: `predictions_canonical_question_group_polymarket_migration_2026_05_06.md` |
| MTDS / SPORTS                    | `league_id` — audit; today MTDS sports manifest has empty `instrument_id` and may be missing `league_id` too                                         |
| features-sports / SPORTS         | `feature_group` — audit; calculator adapter writers need to declare `feature_group=...`                                                              |
| features-onchain / DEFI          | `feature_group` + `chain` — audit                                                                                                                    |
| features-calendar / SHARED       | `feature_group` (per-source) — audit; today single-bucket but feature_group may be empty                                                             |

### deployment-api

- `services/data_status_service.py`:
  - `_BUCKET_TEMPLATES` → already corrected
  - `_SERVICE_CATEGORY_RESTRICTIONS` → already corrected
  - `_SHARED_BUCKET_SERVICES` → already added
  - `_SERVICE_GROUP_AXIS_OVERRIDE` → already added
  - Add `_SHARD_AXIS_MATRIX` consumer + `breakdowns` builder
  - Extend `_get_manifest_status_sync` for `secondary_axis` query param
- `scripts/data_status_rollup_worker.py` — emit new `breakdowns` field in rolled-up coverage payload.

### deployment-ui

- `src/features/data-status/DataStatusTab.tsx` — render `breakdowns`, add axis selector dropdown
- `src/features/data-status/DataStatusGrid.tsx` — secondary-axis query-param wiring

### Migration scripts (one-shot data rewrites)

- No fixture_id backfill — fixture_id dropped from sharding (see rationale in axis matrix).
- No bulk job_id backfill — ML/strategy/execution start fresh; old rows surface under a synthetic `__legacy__` job_id
  key in the UI.
- Per-service feature_group backfills, if audit shows the column is empty, are scoped per-service in their respective
  writer-fix items in Phase 1.

## Phased execution DAG

```
Phase 0 (UAC + UTL schema additions) — no behaviour change
   │
   ├──► Phase 1 (per-service writer updates: populate fixture_id + job_id)
   │       (parallel: sports services, ML/strategy/execution services)
   │
Phase 2 (deployment-api: SHARD_AXIS_MATRIX consumer + breakdowns)
   ├──► (depends on Phase 0)
   │
Phase 3 (deployment-ui: DataStatusTab render)
   ├──► (depends on Phase 2)
   │
Phase 4 (migration scripts: backfill fixture_id for existing sports rows)
   │
Phase 5 (rollup worker: rebuild with new breakdowns; verify on Cloud Run)
   │
Phase 6 (workspace QG sweep + integration smoke test)
```

QG gate between every phase. Phase 4 can run in parallel with Phase 3.

## Phase-by-phase tasks

### Phase 0 — UAC + UTL schema additions

- [x] [UAC] P0. Add `unified_api_contracts/registry/data_status_axis_matrix.py` with `SHARD_AXIS_MATRIX` +
      `DISPLAY_AXES` + `PRIMARY_AXIS` per-(service, asset_group). Lock to the matrix in this plan as initial state.
      Re-export from `unified_api_contracts/registry/__init__.py`. (UAC@2b56dbc — 32 cross-registry tests: asset_group
      keys lowercase, every SHARD has PRIMARY, BREAKDOWN_AXES = SHARD union DISPLAY - {PRIMARY}, DEFI data-pipeline
      services include chain, PREDICTION market-side includes canonical_question_group, experiment services include
      job_id, sports excludes fixture_id from shard atoms.)
- [x] [UAC] P0. Bump availability-manifest schema declaration v6 → v7: add `job_id` (str | None). `fixture_id` is
      **NOT** added. (UTL@ed658e9b — `MANIFEST_SCHEMA_VERSION` 6 → 7 with v7 docstring; UAC has no separate constant for
      the manifest schema version, UTL is the SSOT.)
- [x] [UTL] P0. Update `unified_trading_library/manifests/manifest_writer.py` `_CANONICAL_COLUMNS` to include `job_id`.
      New `add(...)` kwarg: `job_id: str | None = None`. (UTL@ed658e9b — `_ROW_KEY_COLUMNS` already had `fixture_id` +
      `job_id` from `0882b951`; this commit ships the schema-version bump alongside, plus a `_record_status` fix that
      propagates `fixture_id`/`job_id` from `record_empty`/`record_failed` row_keys — they were being dropped before.)
- [x] [UTL] P0. `manifest_reader.py` already tolerates older rows missing newer columns (v4/v5/v6 mix); confirm `job_id`
      is null-safe. (UTL@ed658e9b — `read_availability_index._V6_COLUMNS` renamed to `_V7_COLUMNS` with `fixture_id` and
      `job_id` added; `_backfill()` defaults missing columns to `""` for legacy v1-v6 parquets, surfacing under
      synthetic `__legacy__` job_id key in the deployment-api breakdowns endpoint.)
- [x] [UTL] P0. Add unit tests: write + read with `job_id`; round-trip across schema versions. (UTL@ed658e9b —
      `tests/unit/test_manifest_writer_v7.py` covers default values, `_coerce_row_key` casing preservation, `.add()` +
      `.record_empty()` write paths for ML/sports/strategy adapters, v6→v7 legacy parquet backfill. v6 + league test
      files updated to assert current `MANIFEST_SCHEMA_VERSION == 7`.)

QG gate: UTL + UAC quality-gates pass.

### Phase 1 — Writer updates (per-service)

#### Phase 1 execution principles (codified 2026-05-08 — the (a)/(b)/(c) decision tree)

**Why this section exists**: Phase 0/2/3 shipped the **deliver-with-empty-data** contract — UTL@ed658e9b adds
`fixture_id` + `job_id` columns, deployment-api@85053fe exposes `breakdowns: dict[axis, dict[value, count]]` keyed on
UAC `BREAKDOWN_AXES`, deployment-ui@8056995 renders every declared axis (header + "no data yet" placeholder when empty).
**The UI shape is locked NOW.** Phase 1 fills the data behind it.

The user (operator) sees empty axes today (`league_id` empty for sports / `feature_group` empty for features-\* /
`job_id` empty for ml-training etc.) — Phase 1 lights them up service-by-service, lowest-blast-radius first.

**Per-writer 3-part check** (walk in order; the answer dictates whether the work is a one-line fix or a multi-week
migration):

- **(a) MANIFEST COLUMN** — does the writer pass the new axis as a kwarg into `manifest.record_captured(...)` /
  `manifest.record_empty(row_key={...})` / `manifest.record_failed(row_key={...})`? UTL@ed658e9b accepts `fixture_id` +
  `job_id`; the existing v5 columns (`chain`, `league_id`, `feature_group`, `model_family`, `training_period`,
  `timeframe`, `strategy_id`, `client_id`, `instruction_type`) have been there since the v5 honest-coverage bump. **If
  the writer just isn't passing them → one-line fix per callsite.** Run quality-gates.sh, push, curl
  `/api/data-status/coverage-summary` and confirm the corresponding `breakdowns` dict populates. Done.

- **(b) ON-DISK PARQUET PATH** — does the parquet's hive partition already include this axis, or is it baked into a
  different partition (or worse, into the filename)? **Walk the actual bucket layout before assuming**
  (`gcloud storage ls gs://{bucket}/...` or `/api/data-status/list-files`). Three outcomes:
  - **(b.1)** Path already includes the axis. Examples:
    - Sports per-league: `entity={E}/league={L}/{E}.parquet` already supported per UAC `candidate_parquet_paths`. So
      features-sports `feature_group` is purely a manifest- column add (#a), no path migration.
    - DeFi `chain=` partition: instruments-service migrated 64,060 legacy rows in commit `36261b6` (split venue/chain at
      manifest-write); the path layout already has `chain=ETHEREUM/...` for new writes.
    - `timeframe=` partition: already on every features-\* and MDPS parquet path. → No path change needed. Just (a).
      Done.

  - **(b.2)** Path needs a new partition layer **for new writes only** (legacy data stays where it is, reader falls
    through). Examples:
    - ml-training-service / ml-inference-service: today the parquet path under `gs://ml-training-artifacts-{pid}/` is
      keyed on `model_family` + `training_period` only. Phase 1B `job_id` work needs
      `model_family={M}/training_period={T}/job_id={J}/...` partition for new experiment runs. Old rows (no job_id) keep
      their flatter path; reader probes the new layout first then falls through.
    - strategy-service / execution-service backtest writes: same shape — add `strategy_id={S}/job_id={J}/...` partition
      for new runs; old runs surface under synthetic `__legacy__` job_id key in the breakdowns endpoint (already wired
      in deployment-api@85053fe). → Add the new partition to the writer + extend the reader to probe the new layout
      first, fall back to flatter legacy path. **NO migration script needed** (legacy stays on disk untouched, manifest
      already has flat rows).

  - **(b.3)** Path needs to **MIGRATE** legacy data because the wrong axis was baked into a different partition /
    filename. **STOP — don't do (b.3) inside a Phase 1 writer commit.** It needs its own plan with a one-shot migration
    script + fallback-reader removal, lands in its own PR. Workspace rule **"Manifest migration, NOT fallback"**: the
    only documented exception is hive-vocab `category=` vs `asset_group=` legacy preservation. Examples:
    - Prediction `canonical_question_group`: today encoded as `data_type` (e.g. `data_type=BTC` / `data_type=ETH` /
      `data_type=SPX`) so the manifest collapses 24 hourly markets into one `BTC_UP_DOWN_HOURLY` row. Has its own
      successor plan `predictions_canonical_question_group_polymarket_migration_2026_05_06.md` (multi-week migration).
      DO NOT touch in Phase 1 of this plan. → Precedent migration scripts:
      [`instruments-service/scripts/migrate_local_sfi_to_canonical.py`](../../../../Code/unified-trading-system-repos/instruments-service/scripts/migrate_local_sfi_to_canonical.py),
      [`instruments-service/scripts/migrate_defi_legacy_venue_chain.py`](../../../../Code/unified-trading-system-repos/instruments-service/scripts/migrate_defi_legacy_venue_chain.py).

- **(c) READER** — does any downstream consumer (other services' pre-flight gates, MDPS, features-\*, deployment-ui
  drill-down, deployment-api parquet-download endpoint) need to learn about the new path? Sports + DeFi readers already
  probe candidate paths via UAC SSOT (`candidate_parquet_paths`); ML/strategy/execution readers don't yet exist for the
  experiment data because nobody reads ML training artefacts as a downstream — the only consumer is the data-status
  panel itself, which reads the manifest, not the parquet. So (c) is usually a no-op for the experiment-axis work.

**Principle**: prefer (a)-only fixes. Bump to (b.2) when the axis is genuinely a separate filesystem dimension
(ml/strategy/execution `job_id` is the canonical case). NEVER do (b.3) inside a Phase 1 writer commit — those need their
own plan.

**Per-service execution loop** (do this for each writer — service by service, NOT all at once):

1. **Walk the bucket** — `gcloud storage ls gs://{bucket}/...` or
   `GET /api/data-status/list-files?service=...&asset_group=...&date={recent}` — confirm the actual on-disk path layout.
2. **Decide (a) / (b.1) / (b.2) / (b.3)** per the tree above.
3. **Write the fix** — one-line manifest-kwarg add (a), or partition-layer add (b.2).
4. **Run** `bash scripts/quality-gates.sh` → commit + push to `live-defi-rollout` per the dirty-deps rule (no quickmerge
   required).
5. **Verify breakdowns light up** —
   `curl http://localhost:8004/api/data-status/coverage-summary | jq '.{service}.{asset_group}.breakdowns'` — confirm
   the axis dict populates with real values (not `__legacy__` only).
6. **Move to next service.**

**Highest-leverage order** (these unlock the empty axes the user sees TODAY in the deployment-ui):

1. **MTDS sports** `league_id` — confirm populates on every per-fixture write. Path layout already has `league={L}`, so
   this is **(a)-only**. (See memory: `project_sports_phantom_fixtures_recovery_2026_05_06.md` for full sports manifest
   state.)
2. **features-sports** `feature_group` — each calculator adapter writes `feature_group=` matching the
   upstream-source-keyed bucket (`api_football_only` / `footystats_only` / `understat_only` / `sfi_progressive_only` /
   `cross_source` / `weather`). Audit the 30+ calculators; flag any that omit it. Path layout already has
   `entity={E}/league={L}/...` — confirm whether `feature_group` is encoded somewhere on disk OR is purely a manifest
   column for breakdowns. Purely manifest → **(a)-only**. On-disk in another partition → **(b.2)**.
3. **ml-training-service** `job_id` — derive `job_id = f"{RUN_TS}-{experiment_name}"` at ServiceBootstrap or top-level
   job init, thread through every `manifest.record_captured(job_id=job_id, ...)`. Walk the bucket — does parquet path
   include `job_id=` for new writes? If not, **(b.2)**: extend writer path AND reader fallback. ml-inference / strategy
   / execution follow the same shape.
4. **features-onchain** `feature_group` + `chain` — per calculator (`lending_rates` / `lst_yields` / `gas_fees` /
   `dex_liquidity` / `bridge_events`). DeFi `chain=` partition already exists per the per-asset-group shard-key matrix;
   `feature_group` should be **(a)-only** or **(b.2)**.
5. **features-calendar** `feature_group` — per source (`fred` / `tradingeconomics` / `sec` / `holiday_calendar`).
   Cross-asset shared bucket; verify path layout before assuming.
6. **features-cross-instrument / multi-timeframe** `timeframe` — confirm populates in the manifest. `timeframe=`
   partition already on every features-\* path → **(a)-only**.

**STOP rule**: if a service surfaces a (b.3) case (axis baked into wrong partition → needs migration), STOP and report —
don't try to land it inside a Phase 1 commit. The canonical (b.3) example is predictions `canonical_question_group` —
see the predictions plan, multi-week scope. Open new plan for any other (b.3) discovered.

#### Phase 1A — Per-service shard-axis audit + fixes (parallel)

- [x] [audit] P1. Per-service writer probe: confirm the manifest rows being written today populate the columns listed in
      the SHARD axes column above. Report any that don't. (Audit 2026-05-08 — MTDS sports `league_id` ✅
      [orchestrator.py:2182](../../../../Code/unified-trading-system-repos/market-tick-data-service/market_tick_data_service/engine/orchestrator.py#L2182)
      already passes; features-sports `feature_group` ✅ all calculators already pass per Phase 0.6.G.5 `9874f13`;
      ml-training/inference/strategy/execution `job_id` shipped this session — see Phase 1B below.)
- [x] [MTDS sports] P1. If `league_id` is empty in the MTDS sports manifest, fix the orchestrator/adapter writer to pass
      it on every per-fixture write. (Already (a)-compliant per audit — `league_id_key` flows from shard tuple at line
      2069 through to `manifest.add(league_id=league_id_key)` at line 2188; sentinel paths at 2332/2337 also pass. No
      fix needed.)
- [x] [features-sports] P1. Each calculator adapter writes `feature_group=` matching the upstream-source-keyed bucket
      (`api_football_only`, `footystats_only`, `understat_only`, `sfi_progressive_only`, `cross_source`, `weather`).
      (Already (a)-compliant per audit 2026-05-08 — `batch_handler.py` writers at lines 550-838 +
      `compute_sfi_progressive_only.py` at lines 144/175/233/241 all pass `feature_group=` in row_key.)
- [ ] [features-onchain] P1. Each calculator writes `feature_group=` matching its upstream source (`lending_rates`,
      `lst_yields`, `gas_fees`, `dex_liquidity`, `bridge_events`, etc.) plus `chain=`.
- [ ] [features-calendar] P1. Each source writer (FRED, tradingeconomics, sec, holiday_calendar) populates
      `feature_group`.
- [ ] [features-cross-instrument / multi-timeframe] P1. Confirm `timeframe` populates correctly.

#### Phase 1B — `job_id` writers (parallel with 1A)

- [x] [ml-training-service] P1. ServiceBootstrap or top-level job init: derive `job_id = f"{RUN_TS}-{experiment_name}"`
      (or accept `--job-id` CLI flag); thread through to every `manifest.record_captured(job_id=job_id, ...)`. (Shipped
      2026-05-08 ml-training-service@`f7369f2` — `experiment_id` from CLI handler threaded into
      `TrainingOrchestrator.__init__(experiment_id=...)`, stored as attribute, passed to
      `model_registry.store_model(job_id=...)`, reaches `writer.add(model_family, training_period, job_id)`.
      Construction sites in train_handler / grid_search_handler / final_training_handler updated.)
- [x] [ml-inference-service] P1. Same shape. (Shipped 2026-05-08 ml-inference-service@`69d6313` —
      `PredictionPublisher.__init__` derives `_service_run_id = f"{RUN_TS}-inference"` and threads into both single +
      batch `writer.add()` callsites with `model_family=prediction_event.model_id`.)
- [x] [strategy-service] P1. Backtest CLI / job entry sets `job_id` per backtest run; threads through every shard write.
      (Shipped 2026-05-08 strategy-service@`90e00bb` — `CloudStrategyStorage.__init__` derives
      `_service_run_id = f"{RUN_TS}-strategy"`, threaded into all 3 `writer.add()` callsites — orders / positions / pnl.
      Restarts split rows by service-process boundaries.)
- [x] [execution-service] P1. Backtest CLI same shape. (Shipped 2026-05-08 execution-service@`0b664d99` — two writer
      paths: `save_operations._upload_report_to_gcs` passes `run_id` (already in scope from GCS path partition) as
      `job_id` plus `strategy_id` + `instruction_type` for the v5 columns; live `LiveCloudStorageSink` derives
      `_service_run_id = f"{RUN_TS}-execution-live"` for continuous results.)
- [ ] [tests] P1. Per-service unit test: write under a job_id, assert manifest has populated job_id.

### Phase 2 — deployment-api SHARD_AXIS_MATRIX consumer

- [x] [deployment-api] P2. `services/data_status_service.py`: import `SHARD_AXIS_MATRIX` from UAC. Replace
      `_SERVICE_GROUP_AXIS_OVERRIDE` with `PRIMARY_AXIS` lookup. (deployment-api@85053fe — `_select_coverage_group_axis`
      reads `get_primary_axis(service, cat.lower())` first; `_SERVICE_GROUP_AXIS_OVERRIDE` kept only as a tail fallback
      when the SSOT has no entry for a (service, asset_group) pair.)
- [x] [deployment-api] P2. Add `_build_breakdowns(filtered_index, axes)` helper: for each axis name, returns
      `dict[value, sum(instrument_count)]`. Skip axes where the column is empty across all rows. (deployment-api@85053fe
      — `_build_breakdowns` keyed on UAC `BREAKDOWN_AXES`; empty columns surface as `{}` so the UI renders an "expected,
      no data yet" placeholder rather than hiding the dropdown; empty values collapse under synthetic `__legacy__` key
      for pre-Phase-1B ML/strategy/execution rows.)
- [x] [deployment-api] P2. Wire into `_get_coverage_summary_sync`: per asset_group, look up
      `BREAKDOWN_AXES[(service, cat)]`, build `breakdowns` dict, attach to result. Keep `latest_day_instruments`
      populated from primary axis for backward-compat. (deployment-api@85053fe — `_build_coverage_for_cat` returns
      `breakdowns: dict[axis, dict[value, count]]` alongside the existing `latest_day_instruments` map. Rollup worker
      self-feeds into this path so the next 5-min cron tick lands `breakdowns` in the rolled-up `coverage.json.gz` blob
      automatically.)
- [x] [deployment-api] P2. `_get_manifest_status_sync`: accept new query params `secondary_axis`, `league_id`,
      `fixture_id`, `canonical_question_group`, `job_id`. Apply as filters before building the cell grid.
      (deployment-api@85053fe — `_pack_row_filters` + `_apply_row_filters` helpers; rollup fast-path bypassed when any
      filter is set so filtered queries fall through to the on-demand path. Response echoes `secondary_axis` + `filters`
      back so the UI can confirm the slice it received.)
- [x] [deployment-api] P2. Routes pass query params through; pydantic schema for the new `breakdowns` field.
      (deployment-api@85053fe — `/api/data-status/manifest` accepts the 6 new query params; `breakdowns` is part of the
      existing flexible `dict[str, object]` response shape. New endpoint `/api/config/shard-axis-matrix` exposes the UAC
      SSOT to the deployment-ui axis selector.)
- [x] [deployment-api] P2. Unit tests: per-service breakdown coverage; secondary-axis filtering on manifest endpoint.
      (deployment-api@85053fe — `tests/unit/test_data_status_axis_matrix.py` covers strategy / execution / sports
      primary-axis selection, DEFI chain breakdown, ml-training empty-column behaviour, and `__legacy__` key
      collapsing.)

### Phase 3 — deployment-ui DataStatusTab (FIRST deliverable for the next agent)

**Deliver-with-empty-data principle**: every component below must render gracefully when its breakdown column is empty
(writer hasn't populated it yet). Skeleton + "no data yet" placeholder, not an error toast. The backend writers
(Phase 1) catch up after the UI ships; we want the visual shape locked in first across all 15 services, then data
back-fills behind it.

- [x] [deployment-ui] P3. New `BreakdownsAccordion` component reading the `breakdowns: dict[axis, dict[value, count]]`
      field per asset_group. Empty `breakdowns` → render the axis labels with "no data yet" placeholder, not a blank
      panel. (deployment-ui@8056995 — `src/components/BreakdownsAccordion.tsx` + `BreakdownsAccordion.test.tsx`; 5
      vitest tests covering deliver-with-empty-data invariant, sorted-by-count value rows, `__legacy__` value
      labelling + click skip, axis-count summary in header.)
- [x] [deployment-ui] P3. Per-service-aware axis selector reading the new `/api/config/shard-axis-matrix` endpoint (UAC
      SSOT proxy). Each asset_group panel gets the dropdowns its row dictates: DEFI → chain, sports → league_id,
      strategy/execution → job_id, ML → model_family + training_period, multi-timeframe → timeframe, etc. If the backend
      returns empty values for the dropdown, render an empty selector (disabled state) rather than hiding it.
      (deployment-ui@8056995 — `getShardAxisMatrix(service)` API wrapper + `ShardAxisMatrixResponse` interface;
      `DataStatusTab.tsx` fetches alongside coverage-summary and renders `BreakdownsAccordion` under each asset_group
      card with the axes UAC declares for that pair.)
- [x] [deployment-ui] P3. Cell-grid query passes `secondary_axis` + filter params (`league_id`,
      `canonical_question_group`, `job_id`, `chain`) when the user picks one. Empty matrix from the API → "no shards
      captured for this filter yet" empty-state, not an error. (deployment-ui@`0fbd28b` —
      `manifestFilter: { axis,     value }` state in `DataStatusTab.tsx`, `onSelectValue` handler on
      `BreakdownsAccordion`, `getDataStatusManifest` threads `secondary_axis` + per-axis filter param, `useEffect`
      re-fetches on filter change, active-filter banner with "Clear filter" button surfaces the active state.)
- [x] [deployment-ui] P3. Per-service tab matrix coverage: walk every service in `SHARD_AXIS_MATRIX` and confirm the tab
      renders the right axes per asset_group (especially the experiment-based services where today's manifests are
      mostly empty — we want the job_id selector visible-but-empty so it's obvious how to navigate once data lands).
      (deployment-ui@8056995 — `BreakdownsAccordion` walks the axes list returned by `/api/config/shard-axis-matrix` for
      each rendered asset_group card; empty axes still render with header + "no data yet" placeholder by design, so all
      15 services × applicable asset_groups surface the SSOT shape.)
- [ ] [deployment-ui] P3. Visual regression smoke: Playwright walk across all 15 services × 5 asset_groups (where
      applicable); every tab loads cleanly with the new shape; no console errors; empty-state placeholders render where
      data is absent. **Partially shipped** in deployment-ui@8056995: TypeScript + ESLint + smoke build clean; vitest
      passes for the new component. Full Playwright walk across 15 services × 5 asset_groups deferred to a follow-up
      verification slice.
- [x] [deployment-ui] P3. Document the "expected empty until Phase 1 writers ship" tabs in a doc-comment on
      `DataStatusTab.tsx` so the next reviewer doesn't think the UI is broken. (deployment-ui@8056995 —
      `BreakdownsAccordion.tsx` carries the deliver-with-empty-data principle in its module header docstring;
      `DataStatusTab.tsx` `shardAxisMatrix` state has an inline comment explaining the empty-state policy and the
      silent-fallback behaviour for pre-Phase-2 deployment-api images.)

**Out of scope for Phase 3 (defer to later phases)**:

- Don't write any backend writer code (that's Phase 1).
- Don't gate Phase 3 ship on the rollup worker emitting `breakdowns` (Phase 5). The on-demand path in Phase 2 is
  sufficient for first ship; rollup catches up automatically.

### Phase 4 — Migration scripts

- [ ] (Empty.) No fixture_id backfill (dropped from scope). No bulk job_id backfill — ML/strategy/execution start fresh;
      old rows surface under the synthetic `__legacy__` job_id key.
- [ ] [feature_group backfills] P4. **If** the Phase 1A audit finds a per-service writer that has never populated
      `feature_group`, `chain`, `timeframe`, or `league_id` correctly, write a one-off migration script per affected
      service to backfill from existing parquets. Each migration scoped to its service's repo.

### Phase 5 — Rollup worker rebuild

- [ ] [deployment-api / scripts/data_status_rollup_worker.py] P5. Update worker to emit `breakdowns` in the rollup blob.
      Bump rollup blob schema version to v2 (additive — readers tolerate v1 absence of `breakdowns`).
- [ ] [deployment-service] P5. Push new image to Cloud Run; cron rebuilds 5 min after deploy. Verify rolled-up
      `coverage.json.gz` has `breakdowns`.
- [ ] [deployment-ui] P5. Verify on Cloud Run URL.

### Phase 6 — Workspace QG sweep + integration

- [ ] All affected repos: `bash scripts/quality-gates.sh` clean.
- [ ] Per-service smoke (write + read round-trip with new columns).
- [ ] End-to-end: launch one ml-training experiment (small one) with a job_id, observe the strategy panel showing it.
- [ ] End-to-end: write one sports fixture row via the orchestrator, observe the league + fixture drill-down rendering
      it.

## Success criteria

- Phase 0 gate: UTL `manifest_writer.py` + UAC schema declaration + axis matrix module land on live-defi-rollout. UTL
  unit tests + UAC quality-gates pass.
- Phase 1 gate: sports + ML/strategy/execution writers all populate the new columns on a smoke write. QG passes per
  repo.
- Phase 2 gate: `/api/data-status/coverage-summary?service=instruments-service` includes a `breakdowns` field with
  `chain` for DEFI showing real per-chain counts.
  `/api/data-status/manifest?service=instruments-service&secondary_axis=chain&start_date=...&end_date=...` returns a
  chain-sliced grid.
- Phase 3 gate: deployment-ui DataStatusTab renders the chain-axis dropdown for DEFI without console errors; selecting a
  chain re-issues the API call with the filter and re-renders the grid.
- Phase 4 gate: dry-run report on the migration script shows expected fixture_id row expansion (~hundreds of thousands
  of rows). Live run completes idempotently.
- Phase 5 gate: Cloud Run cron tick rebuilds the rollup; the deployed UI shows the new breakdowns within 10 minutes of
  image promote.
- Phase 6 gate: workspace QG sweep clean; end-to-end smoke green.

## DEFI canonicalisation closeout (2026-05-07)

Closed out the DeFi legacy-underscore venue thread that crossed this plan's scope. UTL `ManifestWriter._coerce_row_key`
now canonicalises legacy underscore venues at write time via UAC `LEGACY_DEFI_VENUE_ALIASES`; the 2026-05-07 MTDS
manifest migration rewrote 411,620 historical rows. The deployment-api read-time fallback
(`_canonicalise_defi_manifest`) is gone.

Commits:

- unified-api-contracts@`405cbf5` — LST/yield protocols + `DEFI_VENUE_PHASE` marker added to `ALL_DEFI_VENUES`.
- unified-api-contracts@`f22f4b1` — `CHAIN_GENESIS_DATES` SSOT in `chain_env.py` (B.3 / P1-C).
- unified-trading-library@`248058bb` — write-time DeFi canonicalisation hook in `_coerce_row_key`.
- unified-trading-library@`25ded4f3` — extends the hook to `ManifestWriter.add()` (the success-capture path was
  initially missed; smoke test confirmed the bug, fix shipped same session).
- market-tick-data-service@`8c3c2c7` — one-shot manifest migration `migrate_mtds_defi_legacy_venue_underscore.py`;
  executed live across 11 DEFI buckets, 411,620 rows rewritten, idempotence verified.
- deployment-api@`64d2be9` — read-time fallback removal; `_canonicalise_defi_manifest` split into
  `_canonicalise_defi_data_types` (data_type alias normalisation only).
- deployment-api@`14bbff9` — wires `CHAIN_GENESIS_DATES` into `_mtds_expected_dates_cached` so per-chain pre-launch
  dates clip out of the DEFI panel's expected denominator.
- unified-trading-pm@`56850b0c` — codex doc refresh: 3 docs trim stale references to legacy underscore venue forms.

Live re-probe across 11 DEFI buckets confirms 0 residual legacy-underscore DeFi-venue rows; only intentional canonical
underscores (TRADER_JOEV2 per UAC `ALL_DEFI_VENUES`) and pre-existing data-type-as-venue bugs (`GAS_FEES` / `LST_RATES`
/ `ORACLE_PRICES`) remain — both out of scope.

Successor for DEFI hyphenated-`data_type` normalisation: still read-time in deployment-api
(`_canonicalise_defi_data_types`); manifests in 6 buckets (`lending-indices`, `dex-pools`, `dex-swaps`, `lst-rates`,
`oracle-prices`, `perp-funding`) still carry hyphenated `data_type` values. No paired migration script for that side yet
— natural Plan B follow-up.

## Temporary states + their canonical follow-up plans

- **No existing job_id on ML/strategy/execution data** — Phase 1B writes start populating; old data has null job_id and
  shows under a synthetic `__legacy__` job_id key in coverage-summary. No bulk backfill — old experiment runs without
  job_id are out of scope.
- **deployment-ui tabs without per-service axis SSOT load** — Phase 3 introduces UI SSOT via
  `/api/config/shard-axis-matrix`. Until shipped, the UI uses the previous flat axis behaviour as a fallback. Successor
  deletion: remove fallback in Phase 3 final commit.
- **Mixed schema versions in the manifest** (v4/v5/v6) — already on the staircase from earlier migrations. Phase 0 v6→v7
  follows the same additive pattern. No bulk re-migration needed; readers tolerate older rows via null fallback.
- **Prediction `canonical_question_group` encoded as `data_type`** — successor:
  `predictions_canonical_question_group_polymarket_migration_2026_05_06.md`.

## What this plan does NOT do (out of scope)

- **instrument_type sharding for instruments-service or MTDS bulk fetches**. Databento (TradFi) and TARDIS (CeFi) both
  fetch all instruments per venue/exchange in bulk; sharding by instrument_type would mean the same fetch + filter 20× —
  pure waste. instrument_type is kept as a row column for filter/group only. (MTDS per-instrument-id sharding is
  separate and remains, justified by memory.)
- **`fixture_id` as a shard atom**. `(league_id, day)` already bounds the fixture set per cell; per-fixture detail comes
  from the parquet at drill-down time, not the manifest. Avoids inflating the sports manifest.
- **TradFi/DeFi instrument_type per-instrument migration for instruments-service**. Today's flat per-venue file is
  deliberate.
- **Cluster validation surfacing** for bundled shards (ES.OPT 11-cluster, futures_chain, prediction
  canonical_question_group bundles) — covered by `writegate_honest_coverage_endtoend_2026_05_06.md` Phase 1A.
- **`client_id` semantics rework**. Already in v6; keeps its multi-tenant scoping meaning. `job_id` is added alongside,
  not as a replacement.
- **Operations-dropdown CLI derivation** — covered by `data_status_operations_dropdown_cli_derived_2026_05_07.md`.

## References

- Per-asset-group shard-key matrix — CLAUDE.md SSOT
- Companion writer plan: `shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md`
- Honest-coverage write-gate: `writegate_honest_coverage_endtoend_2026_05_06.md`
- Feature DAG SSOT: `feature_dag_uac_ssot_and_features_coverage_2026_05_06.md`
- This session's incremental fixes (already shipped, not part of this plan):
  - Coverage-summary correctness (instrument_count sum, drop date='all', drop future-dated, drop empty venues)
  - Coverage-summary axis swaps (sports → data_type, strategy → strategy_id, execution → instruction_type, ml →
    model_family)
  - `_SHARED_BUCKET_SERVICES` for cross-asset features (calendar, ml-training, ml-inference)
  - Bucket-template fixes (ml-training-artifacts, strategy-store-{cat}, execution-store-{cat})
  - Per-service `_SERVICE_CATEGORY_RESTRICTIONS` applied to coverage-summary
  - DEFI legacy venue/chain split + 64,060-row migration
  - PANCAKESWAP_V3-ZKSYNC purge
