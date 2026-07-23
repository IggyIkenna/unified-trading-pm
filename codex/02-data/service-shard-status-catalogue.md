---
doc_type: codex-ssot
title: Service shard-status catalogue (data-catalogue.*.yaml) — the shape deployment-api actually consumes
summary: >-
  The real, as-implemented schema of the 17 per-service `data-catalogue.{service}.yaml` files: a
  `shard_status[ASSET_GROUP][VENUE]` tree whose `start_date` deployment-api reads as the instruments-service GENESIS
  date, and whose venue keys ARE the configured-venue universe per asset_group. Also records what is NOT true of these
  files — they are 5.5 months stale, `auto_refreshed` is null, and the refresher `sync-catalogue-yaml.py` reads a GCS
  artifact that no writer in the workspace produces. Replaces `data-catalogue-schema.md`, which documented an artifact,
  writer, reader, updater and validating plan that do not exist.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, deployment-api, instruments-service]
scope: [engineer, admin]
tags: [catalogue, data-status, shard-status, genesis, reference-data, ssot, staleness]
related:
  [
    data-catalogue-schema.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/cross-asset-canonical-target-ssot.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: 2026-07-20
authoritative_for:
  [
    data-catalogue.*.yaml live schema,
    shard_status genesis + configured-venue universe,
    data-catalogue staleness + missing-writer state,
  ]
referenced_by: [/codex/02-data/data-catalogue-schema.md]
owner:
last_reviewed: 2026-07-20
code_refs:
  [
    deployment-api/deployment_api/services/data_status/reference_scope.py,
    unified-trading-pm/scripts/catalogue/sync-catalogue-yaml.py,
    unified-trading-pm/configs/,
  ]
supersedes: data-catalogue-schema.md
---

# Service shard-status catalogue — the live `data-catalogue.*.yaml` shape

> **What this is.** The **as-implemented** SSOT for the 17 per-service
> `unified-trading-pm/configs/data-catalogue.{service}.yaml` files (symlinked into `deployment-service/configs/`). It
> replaces [`data-catalogue-schema.md`](data-catalogue-schema.md), which specified a `datasets:` list plus a writer,
> reader, updater and validating plan that were **verified absent from the workspace on 2026-07-20** and whose field set
> has **zero overlap** with the live files.
>
> This doc describes only what a live consumer actually reads. It deliberately does not propose a target schema — that
> is a design decision, not a documentation one.

---

## 1. The live top-level shape

Every `data-catalogue.{service}.yaml` carries these keys (verified across all 17 files):

```yaml
service_name: market-tick-data-service # repo name of the owning service
last_updated: "2026-02-06" # date string — hand/script stamped
auto_refreshed: "2026-02-06T12:35:00" # ISO ts, or `null` where never refreshed
status: SPRINT STARTING POINT # FREE TEXT, not an enum
known_exceptions: # free-text operator notes, not a typed set
  - "CEFI: TARDIS API issue -- data exists but gaps remain"
catalogue_dimensions: # the axes shard_status is keyed on
  - category
  - venue
  - instrument_type
  - data_type
  - date
shard_status: # ← the only machine-consumed section
  CEFI: ...
```

**Only `shard_status` has a machine consumer.** `status` and `known_exceptions` are free-text operator prose;
`catalogue_dimensions` is descriptive. Nothing validates any of it — there is no schema validator for these files in the
workspace.

## 2. `shard_status` — the tree deployment-api reads

```yaml
shard_status:
  CEFI: # asset_group key, UPPERCASE
    _status: "49.1% -- venue-level gaps" # underscore-prefixed = SECTION METADATA, not a venue
    _sample_period: "2025-01-01 to 2025-01-31"
    BINANCE-SPOT: # venue key, UPPERCASE; role-qualified or base
      instrument_types:
        SPOT_PAIR:
          data_types: [trades, book_snapshot_5]
          start_date: "2019-03-30" # ← THE consumed field
          stage_1_has_run: true
          stage_2_data_complete: false
          completion_pct: 58.1
          latest_data_date: null
          assignee: ""
          notes: "58.1% -- 18/31 dates in Jan 2025."
```

**Note the two `start_date` depths.** In `data-catalogue.market-tick-data-service.yaml` the `start_date` sits under
`shard_status[AG][VENUE].instrument_types[IT]`; the deployment-api consumer reads it at
`shard_status[AG][VENUE].start_date` — one level shallower. The two files are not the same shape at that depth, and the
consumer reads only the instruments-service file (§3). Do not assume a uniform depth across the 17 files.

## 3. The one real consumer — deployment-api reference scope

`deployment-api/deployment_api/services/data_status/reference_scope.py` reads
**`data-catalogue.instruments-service.yaml`** only (`_CATALOGUE_FILENAME`, :42) and extracts exactly one thing:

```
shard_status[ASSET_GROUP][VENUE].start_date   →   {(AG_UPPER, VENUE_UPPER): genesis_date_str}
```

`_parse_genesis_map` (:54-77) walks the tree, upper-cases both keys, and keeps only non-blank string `start_date`
values. `_load_genesis_map` (:80-96) caches the result process-wide; `reset_genesis_cache()` is the test/hot-reload
seam.

**It carries TWO meanings, and both matter:**

1. **Genesis** — the earliest date at which a `(asset_group, venue)` could have data. A purely pre-genesis day is
   genuinely `out_of_scope`.
2. **The configured-venue universe** — `reference_genesis()` returns `None` **⟺ the venue is not a configured
   instruments-service venue for that asset_group**, i.e. the YAML's venue KEYS are themselves the in-scope venue list
   (:120-140). A configured venue that is simply MISSING data stays **in-scope + missing** — a real, actionable
   denominator gap. An unlisted venue is `out_of_scope`.

**Venue-token reconciliation**: the IS catalogue lists BASE exchanges (`COINBASE`, `OKX`) while the market-data manifest
qualifies them by market role (`COINBASE-SPOT`, `OKX-FUTURES`, `OKX-SWAP`). `reference_genesis()` tries the exact token
first, then strips a trailing role suffix from `_VENUE_ROLE_SUFFIXES`
(`-SPOT`/`-FUTURES`/`-SWAP`/`-PERP`/`-PERPETUAL`/`-COMBO`, :109 + `_base_venue_token` :112-118) so a configured venue is
not flagged out-of-scope merely for its suffix. **Any consumer joining manifest venues to this catalogue must do the
same base-token fallback.**

**Grain is `(venue, day)`.** Per-`instrument_type` scoping is explicitly NOT attempted here (module docstring :23-24) —
it is tied to a manifest-schema change.

Why this file at all: instruments-service and corporate-actions emit REFERENCE data as one bundled `(venue, day)`
parquet recorded with `data_type=""`. That token is in neither the market-data `EXPECTED_COVERAGE_BY_ASSET_GROUP`
registry nor `PROCESSED_REQUIRES_RAW`, so the market-data scope check classified **every** reference row as
`out_of_scope`. The catalogue is the correct scope source for a reference-bundle service (docstring :1-21).

## 4. Staleness + the missing writer (read before trusting any number here)

**These files are stale and nothing is refreshing them.** Verified 2026-07-20:

| Fact                                                                     | Evidence                                                     |
| ------------------------------------------------------------------------ | ------------------------------------------------------------ |
| `data-catalogue.instruments-service.yaml` → `last_updated: "2026-02-06"` | The file itself, line 2 — ~5.5 months stale                  |
| Same file → `auto_refreshed: null`                                       | Line 3 — the auto-refresh has **never** run for this service |
| No writer exists for the artifact the refresher reads                    | See below                                                    |

`unified-trading-pm/scripts/catalogue/sync-catalogue-yaml.py` is the refresher. It queries, via DuckDB,
`read_parquet('gs://{data-catalogue-<project_id>}/**/manifest.parquet', hive_partitioning=true)`
(`_build_catalogue_query`, :37-49) and merges the aggregate back into `shard_status` (:104-110). **A workspace-wide
search on 2026-07-20 found no writer of `gs://data-catalogue-{project_id}/**/manifest.parquet`** — the only hits on
`data-catalogue-` are this reader, `sync-to-mock.py`, docs, and plans. The retired `data-catalogue-schema.md` claimed
`deployment_service.data_status.manifest_writer.ManifestWriter` wrote it; **that package does not exist**.

**Consequences you must respect:**

- `completion_pct`, `latest_data_date`, `stage_*` and `_status` are a **2026-02-06 snapshot**, not live state. Never
  report them as current coverage. Live coverage comes from the availability manifest —
  [`availability-manifest-and-data-status.md`](availability-manifest-and-data-status.md) and the formula in
  [`honest-coverage-model.md`](honest-coverage-model.md).
- `start_date` is the exception worth trusting: a venue's genesis is a historical fact that does not go stale. This is
  why the one live consumer reads only that field.
- **Whether to build the missing writer, retire `sync-catalogue-yaml.py`, or replace the catalogue with a manifest
  projection is an OPEN question** — it is not ruled here.

## 5. Not to be confused with the availability manifest

Two different artifacts historically shared the class name `ManifestWriter`:

- **This catalogue** — per-service YAML, operator-facing inventory + genesis, `(venue, day)` grain, no live writer.
- **The availability manifest** — `gs://{kind}-{asset_group}-{env}-{project_id}/_index/availability_index.parquet`,
  written via `unified_trading_library.manifest_writer.ManifestWriter`
  (`record_captured`/`record_empty`/`record_failed`/`record_expected_unattempted`), per-shard `capture_status` × typed
  `error_reason`. SSOT: [`availability-manifest-and-data-status.md`](availability-manifest-and-data-status.md).

When in doubt: the **availability manifest** is the May-23 cutover artifact and the live 4-state ledger; this catalogue
is the reference-scope + genesis lookup.
