---
doc_type: plan
title: Manifest consolidator — fix dtype-at-source (stops persisting instrument_count/etc. as utf8)
summary:
  The canonical availability index (`_index/availability_index.parquet`) gets written with instrument_count/row_count/
  expected/available as STRING by the manifest consolidator (root cause of the prediction+sports capture-death
  incident). The UTL reader-side coercion crash-proofs the merge, but the canonical index itself should be honest — find
  where the consolidator's DuckDB merge loses the schema and fix it at the source.
status: draft
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-library, market-tick-data-service]
scope: [engineer]
tags: [manifest, consolidator, dtype, duckdb, schema, parquet]
related:
  [
    plans/active/issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md,
    plans/active/prediction_capture_incident_remediation_2026_07_06.md,
    plans/active/issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md,
    codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: 2026-07-07
last_updated: 2026-07-07
parent_epic: instruments_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  [
    split from prediction_capture_incident_remediation_2026_07_06.md Workstream A residuals,
    2026-07-07 — operator requested AO-ready split; born draft,
    flip to active once AO updates land,
  ]
---

# Manifest consolidator — fix dtype-at-source

> **⚠️ CORRECTED 2026-07-14 (doc-reconciliation verify-rerun-2, finding 147)** — this banner's "nothing is on fire"
> framing is now stale/false: a 2026-07-12 production incident
> (`issues/tradfi_manifest_consolidator_row_count_varchar_crash_2026_07_12.md`) crash-looped the tradfi/cefi/prediction
> manifest-consolidator Cloud Run jobs for ~85-90 minutes on the same VARCHAR row_count/instrument_count defect class in
> the same `manifest_consolidator.py` module — a different code path (the `cf2e196b` window-`ORDER BY` `COALESCE`, fixed
> via `TRY_CAST` in `bb17638e`) than the `_merge_dataframes` write-side coercion this banner cites, proving that
> coercion does NOT "crash-proof every reader" against this defect class as claimed. This dtype-at-source fix is still
> unshipped (`status: draft`, all todos below unchecked) and remains the correct root-cause fix; treat this as more
> urgent than "nothing is on fire" implies. (was: "Not urgent — the UTL write-side coercion (`_merge_dataframes`,
> unified-trading-library@6c090bb/@1651340) already crash-proofs every reader against this, so nothing is on fire.")
>
> This is a correctness/honesty fix: the CANONICAL index should carry typed columns, not utf8. Background + the incident
> this caused: `issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md`.

## What's already known (verified — don't re-derive)

- **The consolidator runs as** `python -m unified_trading_library.manifest_consolidator --bucket <bucket>`, deployed
  inside the **`market-tick-data-service`** Cloud Run image (`uts-prod-manifest-consolidator-instruments-*` jobs) — the
  logic lives in UTL, but the DEPLOYED image is `market-tick-data-service`. If the fix needs a `BASE_IMAGE_DIGEST` pin
  bump to reach the running jobs, mirror the exact recipe from instruments-service@1098731c4 (bump the pin to the fixed
  UTL base, redeploy, verify via `docker`-inspecting the rebuilt image before trusting a cloud re-run).
- **The write path is DuckDB, not pandas** (`_duckdb_consolidate_and_write`,
  `unified_trading_library/manifest_consolidator.py:1286`) — per the consolidator SSOT, this was a deliberate perf
  choice (pandas concat/sort/dedup OOM'd the 16GiB job on the cefi flat merge).
- **A concrete lead, NOT yet confirmed as the root cause** — `manifest_consolidator.py:325`:
  `coalesce(nullif(cast({col_expr} AS VARCHAR), ''), '{_DEDUP_NULL_SENTINEL}')` casts a column to VARCHAR to build a
  null-safe dedup-key/ordering expression. This is a legitimate pattern IF scoped to an internal ranking/dedup
  expression that never reaches the output SELECT — but if this (or a similar VARCHAR-cast helper) leaks into the
  columns actually written to parquet (directly, or via a `SELECT *`-style expansion that inherits the cast column's
  type), that would explain exactly the observed symptom (string-typed `instrument_count` etc. in the canonical index).
  **Not traced end-to-end yet — this is the first thing to check, not an assumed conclusion.**

## Todos

- [ ] [DATA] P1. Trace the DuckDB merge in `_duckdb_consolidate_and_write` (and any helper it calls, e.g. the one at
      line 325) end-to-end to find exactly where `instrument_count` / `schema_version` / `row_count` / `expected` /
      `available` / `expected_window_completeness_fraction` lose their native type before landing in the written
      parquet. Confirm or rule out the line-325 VARCHAR-cast lead specifically. Reproduce locally against a real
      string-poisoned bucket (e.g. `instructions-store-sports-prd-…` or `-pred-prd-…`, both currently poisoned — see the
      issue doc) before writing a fix, so the fix is verified against the actual failure mode, not a synthetic one.
      Gate: the exact SQL/expression responsible for the type loss is identified + cited (file:line).
- [ ] [CODE] P1. Fix it so the consolidator persists schema-typed columns (int/bool/float, not utf8) — cast back to the
      correct type in the final SELECT, or avoid the lossy cast in the first place, whichever the trace in the prior
      todo points to. Get the fix into the `market-tick-data-service` image (base-pin bump + rebuild if the fix lands in
      UTL — same recipe as instruments-service@1098731c4; docker-inspect the rebuilt image to CONFIRM the fix landed
      before trusting a cloud re-run, per the lesson from that same incident). Gate: a fresh consolidator cycle
      (`uts-prod-manifest-consolidator-instruments-{sports,prediction}` or a manual `consolidate(bucket, force=True)`
      run) writes `_index/availability_index.parquet` with `instrument_count` etc. as native int/bool/float dtypes —
      verified by directly reading the parquet and checking `.dtypes`, not by trusting a green exit code alone.
      `Evidence: cloudbuild=<id>` for the image rebuild.

## Done definition

A fresh consolidator run on a previously-poisoned bucket (sports or prediction) writes the canonical index with typed
columns, verified by direct parquet read; `quality-gates.sh`-green + quickmerge on every code change.
