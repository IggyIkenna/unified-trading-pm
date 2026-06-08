---
title:
  "BigQuery as an optional feature/ML compute engine over the hive-partitioned GCS corpus — scale path alongside
  in-process polars/DuckDB"
created: 2026-06-08
parent_epic: epics/features_and_ml_master.md
assigned_vm: vm-ml
status: active
priority: P2
estimate_class: design
estimate_baseline_ai_days: 7
estimate_calibrated_ai_days: 4.2
locked_by: live-defi-rollout
locked_since: 2026-06-08
source:
  - operator 2026-06-08 ("for performance we want an OPTION to use BigQuery to process features + ML — the whole point
    of hive partitions is this")
  - composes with codex/06-coding-standards/data-engine-selection.md + read-time-filter-pushdown.md
---

# BigQuery as an OPTIONAL feature/ML compute engine

> **The whole point of the hive partitions** (`asset_group=/pipeline_mode=/source=/data_type=/timeframe=/day=`) is that
> the corpus is queryable at scale with **partition pruning** — which is exactly what a warehouse engine wants. For
> large feature recomputes + ML training/feature-extraction, an in-process polars/DuckDB pass over millions of parquet
> files is the bottleneck; **BigQuery over the same partitions** prunes to the needed cells and parallelises
> server-side.
>
> **This is an OPTION, not a replacement** — an engine-selection toggle (extends the existing DuckDB-vs-polars
> `data-engine-selection` codex with a third tier: BQ). In-process stays the default for small/live/low-latency; BQ is
> for large batch feature recomputes, cross-instrument joins, and ML at corpus scale.

## Why it fits the architecture

- The GCS parquet is already **hive-partitioned** → BigQuery **Hive-partitioned external tables** (or BQ-managed tables
  loaded from the partitions) map 1:1, with partition pruning on `asset_group/data_type/timeframe/day` so a query scans
  only the cells it needs (cost = bytes scanned, so pruning = cheap).
- The canonical v9 schema (post-migration) is uniform per data_type → a stable external-table schema per
  `(asset_group, data_type)`.
- Features are largely windowed aggregations + joins → expressible as BQ SQL; ML via **BQML** (train/predict
  in-warehouse) or BQ-as-feature-store feeding the existing ML pipeline.

## Design — a third engine tier (toggle), not a fork

- [ ] [DESIGN] P1. **Engine-selection extension** — add `BIGQUERY` to the engine selector (codex
      `data-engine-selection.md`): in-process polars (small/live) → DuckDB (medium, memory-bound) → **BigQuery (large
      batch / corpus-scale / cross-instrument)**. Selection by data volume + job type, not a hard switch; same
      feature/output CONTRACT regardless of engine (batch=live + canonical schema unchanged).
- [ ] [INFRA] P1. **Hive-partitioned external tables** — Terraform + a registration script that defines a BQ external
      table per `(asset_group, data_type)` over the canonical GCS prefix with `hive_partition_uri_prefix` + partition
      schema; verify pruning (a 1-day query scans ~1 day of bytes, not the corpus). Read-only over GCS — no data copy
      for the external path.
- [ ] [CODE] P2. **Feature compute on BQ** — a BQ-SQL expression path for the delta_one feature registry (start with the
      windowed/aggregation groups that translate cleanly; the registry's `formula_version` stays the SSOT — BQ is an
      alternate executor of the SAME formula, asserted equal to the polars path on a fixture). NOT all 1,382 specs day-1
      — the subset that benefits from scale.
- [ ] [CODE] P2. **ML path** — BQML for training/inference at corpus scale OR BQ as the feature store feeding
      ml-service; decide per model. Feature parity with the in-process path is the gate (same features → same model
      inputs).
- [ ] [CODE] P2. **Output back to canonical GCS** — BQ results written back as canonical v9 parquet (same
      schema/pipeline_mode/source/manifest emission) so downstream is engine-agnostic; the manifest records the cells
      identically whether polars or BQ produced them.
- [ ] [DATA] P3. **Cost guardrails** — per-job byte-scanned budget + require partition filters (reject an unpruned
      full-corpus scan); clustering on `(venue, instrument)` within day-partitions to cut scanned bytes; a cost log.
- [ ] [DATA] P3. **Benchmark** — a large feature recompute (e.g. the bar-edge `features-*` corpus purge) run both ways;
      record wall-clock + cost; codify the volume threshold where BQ wins into `data-engine-selection.md`.

## Boundaries / non-goals

- **Not the live/low-latency path** — live feature compute stays in-process (BQ latency + cost wrong for per-tick).
- **Not a second source of truth** — BQ reads the canonical GCS corpus + writes canonical parquet back; GCS + the
  manifest remain SSOT. No BQ-only datasets that downstream must special-case.
- **Cloud-agnostic note** — GCP BigQuery here; the AWS-fleet equivalent (Athena/Redshift Spectrum over the same hive
  layout) is a parallel option if/when needed — same external-table-over-hive-partitions principle. Track separately.

## Composes with

`codex/06-coding-standards/data-engine-selection.md` (the engine tiers — this adds BQ) · `read-time-filter-pushdown.md`
(partition pruning is the same idea at warehouse scale) · the bar-edge corpus recompute
(`bar_edge_left_vs_right_remediation_2026_06_08.md` Phase 2 — a candidate first BQ workload) · the canonical v9 schema
(the stable external-table schema depends on the migration landing first).

## Open questions (operator)

1. **Scope of the feature-SQL path** — translate the whole delta_one registry to BQ-SQL, or only the scale-bound groups
   (cross-instrument, long-window)? Recommend the scale-bound subset first, with the formula_version asserted equal.
2. **BQML vs BQ-as-feature-store** for ML — train in-warehouse, or BQ feeds ml-service? Likely per-model.
3. **Sequencing** — this depends on the canonical v9 migration landing (stable schema). Gate after the per-AG `--apply`.
