---
doc_type: plan
title: Manifest consolidator — fix dtype-at-source (stops persisting instrument_count/etc. as utf8)
summary:
  The canonical availability index (`_index/availability_index.parquet`) gets written with instrument_count/row_count/
  expected/available as STRING by the manifest consolidator (root cause of the prediction+sports capture-death
  incident). The UTL reader-side coercion crash-proofs the merge, but the canonical index itself should be honest — find
  where the consolidator's DuckDB merge loses the schema and fix it at the source.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-library, market-tick-data-service]
scope: [engineer]
tags: [manifest, consolidator, dtype, duckdb, schema, parquet]
related:
  [
    /plans/archive/issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md,
    /plans/active/prediction_capture_incident_remediation_2026_07_06.md,
    /plans/archive/issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: 2026-07-07
last_updated: 2026-07-25
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

> **🟢 RESOLVED 2026-07-25 (sub-agent verification pass)** — traced the write path end-to-end, RULED OUT the
> line-325-era `_dedup_key_sql` VARCHAR-cast lead (it's scoped to dimension/dedup-key columns only, never the numeric
> metric columns), and confirmed the actual root cause + fix already shipped under the sibling incident-response commits
> this doc's own banner cites: `unified-trading-library@02fc4661` (2026-07-21) added `_TYPED_MANIFEST_COLUMNS` +
> `_typed_col_projection()` — TRY_CAST-pinning `instrument_count`/`row_count`/`schema_version`/
> `expected_window_completeness_fraction`/`expected`/`available` to their declared type at BOTH the per-shard scan AND
> the canonical read, before either side ever reaches a `UNION ALL` — generalizing the row_count (`bb17638e`,
> 2026-07-12) and schema_version (`ac051bfe`, 2026-07-20) point-fixes into one dtype-at-source guard covering every
> declared-numeric/bool manifest column. This landed and was ALREADY DEPLOYED before this session started (nobody had
> linked it back to this plan, which is why it stayed `status: draft`) — see the "What I verified" section below for the
> exact trace, the redeploy-currency proof, and the live-parquet dtype verification against BOTH previously- poisoned
> buckets (sports + prediction) named in this doc. No new code was needed or written. See background:
> `issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md` (archived, resolved).
>
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
  logic lives in UTL, but the DEPLOYED image is `market-tick-data-service`.
- **The write path is DuckDB, not pandas** (`_duckdb_consolidate_and_write`,
  `unified_trading_library/manifest_consolidator.py:3093`, calling `_duckdb_merge_payload` at `:2368` and
  `_write_consolidated` at `:3131`) — per the consolidator SSOT, this was a deliberate perf choice (pandas
  concat/sort/dedup OOM'd the 16GiB job on the cefi flat merge). (Line number for `_duckdb_consolidate_and_write` has
  shifted from `:1286` as the module grew — cite `:3093` going forward.)
- **The line-325-era VARCHAR-cast lead is RULED OUT** — now `_dedup_key_sql` at `manifest_consolidator.py:551`
  (`coalesce(nullif(cast({col_expr} AS VARCHAR), ''), '{_DEDUP_NULL_SENTINEL}')`). Confirmed by grepping every call site
  (`:2509`, `:2535-2537`, `:2793-2795`, `:2798-2799`): it is applied ONLY to `dedup` — `_BASE_DEDUP_COLS` (`date`,
  `venue`, `data_type`, `service_name`, `:523`) + whichever `_OPTIONAL_DEDUP_COLS` (`timeframe`, `league_id`, `chain`,
  `instrument_type`, `underlying`, `feature_group`, `model_family`, `training_period`, `strategy_id`, `client_id`,
  `instruction_type`, `instrument_id`, `:524-537`) are present — i.e. dimension/identity columns used only inside
  `PARTITION BY` / `ANTI JOIN` key-match expressions. It never touches `instrument_count`/`row_count`/`schema_version`/
  `expected`/`available`/`expected_window_completeness_fraction` and never reaches the output `SELECT`. Legitimate
  pattern, not the bug.

## What I verified (2026-07-25, sub-agent pass — the fix already shipped; no new code was needed)

**Root cause (confirmed, file:line):** DuckDB's `read_parquet(..., union_by_name=true)` + `UNION ALL` merge (both the
per-shard scan and the canonical read feeding every downstream CTE) silently promotes a declared-numeric/bool column to
VARCHAR the instant EITHER side stores that column as a string for even one row — poisoning the WHOLE merged column
corpus-wide, because DuckDB widens a UNION's mismatched-type column to the common supertype (VARCHAR) rather than
erroring. Exactly the mechanism already root-caused (for the narrower `row_count`/`schema_version` cases) in
`issues/tradfi_manifest_consolidator_row_count_varchar_crash_2026_07_12.md` and
`issues/tradfi_schema_version_string_regression_2026_07_20.md` (both archived, resolved).

**Fix (already landed, generalized to every declared-typed column):** `unified_trading_library/manifest_consolidator.py`
— `_TYPED_MANIFEST_COLUMNS` dict (`:594`: `schema_version`/`row_count`/`instrument_count` → `BIGINT`,
`expected_window_completeness_fraction` → `DOUBLE`, `expected`/`available` → `BOOLEAN`) + `_typed_col_projection()`
helper (`:604`), applied at BOTH the per-shard scan (`shard_proj`, `:2719`) and the canonical read (`canon_proj`,
`:2779`) via `TRY_CAST(col AS <type>) AS col` (present) / `CAST(NULL AS <type>) AS col` (absent) — pinning BOTH sides of
every subsequent `UNION ALL` to the SAME explicit type before they ever meet, so a single VARCHAR-poisoned shard can
never again promote the merged column. This projection is inherited through every downstream branch (incremental
anti-join `:2866`, chunked date-range concat `:3017`, full-rebuild window-dedup `:3057`, Option-B collapse `:3040`) all
the way to the final `COPY (...) TO '...' (FORMAT parquet)` writes — the coercion happens at the EARLIEST read (source),
not patched after the fact. Shipped `unified-trading-library@02fc4661` (2026-07-21, anti-regression test
`tests/unit/test_manifest_consolidator_numeric_varchar_hardening.py`), further hardened for an unrelated TOCTOU race at
`unified-trading-library@14301571` (2026-07-24). This is the SAME fix the schema_version incident doc's own P2 follow-up
recommended and tracked as shipped.

**Redeploy currency (confirmed live, no action needed):** the running Cloud Run jobs
(`uts-prod-manifest-consolidator-instruments-{sports,prediction}`) reference `market-tick-data-service:latest` and
resolve that mutable tag FRESH at every execution start — confirmed via
`gcloud run jobs executions describe uts-prod-manifest-consolidator-instruments-sports-mlzjz --project central-element-323112 --region asia-northeast1 --format=json`
(execution started 2026-07-25T22:48:02Z) showing the resolved container image
`market-tick-data-service@sha256:bcd89e69d2ea3307defaf70ba089c4ea2ed930f586b75318d721d33ea240bf04`. That digest is
`market-tick-data-service:latest`, built 2026-07-25T22:35:18Z from `market-tick-data-service@b444608`, whose
`Dockerfile:125` pins `ARG BASE_IMAGE_DIGEST=sha256:b005050e4e45ddddd79c870c6de060debd3517ac8e076739e8bff03ef9d21f4a` =
`unified-trading-library` tag `0.57.0-4e696d327b63` (`unified-trading-library@4e696d32`) — confirmed via
`git -C unified-trading-library show 4e696d32:unified_trading_library/manifest_consolidator.py | grep -n '_TYPED_MANIFEST_COLUMNS\|_typed_col_projection'`
that this exact pinned commit already carries the fix. So the fix has been live in production since before this session.

**Live-parquet dtype verification (the todo-2 gate, exact command + output):**

```
$ gcloud storage cp gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet ./sports_availability_index.parquet
$ gcloud storage cp gs://instruments-store-pred-prd-central-element-323112/_index/availability_index.parquet ./pred_availability_index.parquet
```

Both are genuinely fresh writes from the LIVE consolidator cron (sports: GCS generation `1785019456171804`, written
`2026-07-25T22:44:16Z`; prediction: generation `1785019721960244`, written `2026-07-25T22:48:41Z`) — both the exact two
"currently poisoned" buckets this doc named.

```python
>>> import pyarrow.parquet as pq
>>> pq.read_schema("sports_availability_index.parquet")
instrument_count: int64
row_count: int64
schema_version: int64
expected_window_completeness_fraction: double
expected: bool
available: bool

>>> pq.read_schema("pred_availability_index.parquet")
instrument_count: int64
row_count: int64
schema_version: int64
expected_window_completeness_fraction: double
expected: bool
available: bool
```

Confirmed further at the Python-value level (`pyarrow.Table.column(...).to_pylist()`) that every non-null value in every
one of these 6 columns is a genuine `int`/`bool` object — sports: 5,584,073 rows scanned, `instrument_count` sample
`[0, 0, 0, 0, 0]` type `int`, `expected`/`available` sample `[True, True, ...]`/`[False, False, ...]` type `bool`;
prediction: 27,341 rows, `instrument_count` sample `[123, 0, 0, 6, 1]` type `int`. (A plain
`pandas.read_parquet(...).dtypes` shows `float64`/`object` for `instrument_count`/`expected`/`available` on the sports
file — a well-known pandas/pyarrow NaN-upcast interop artifact from the ~296k nulls in that column, NOT a recurrence of
the string-poisoning bug; the arrow-schema + per-value-type check above is the unambiguous source of truth and is what
this evidence cites.)

**Conclusion:** the dtype-at-source fix this plan tracks is fully shipped, deployed, and verified against real
production data on both named buckets. No new code was written this session — the fix landed under
`unified-trading-library@02fc4661`/`@14301571` (sibling incident-response commits nobody had linked back to this plan,
which is why it sat `status: draft`).

## Todos

- [x] [DATA] P1. Trace the DuckDB merge in `_duckdb_consolidate_and_write` (and any helper it calls) end-to-end to find
      exactly where `instrument_count` / `schema_version` / `row_count` / `expected` / `available` /
      `expected_window_completeness_fraction` lose their native type before landing in the written parquet. — **DONE
      2026-07-25.** `_dedup_key_sql` (the line-325-era lead, now `:551`) RULED OUT — scoped only to dimension/dedup-key
      columns (`:523-537`), never the numeric metric columns, never reaching the output SELECT. Actual cause: DuckDB's
      `union_by_name` + `UNION ALL` promotes a declared-typed column to VARCHAR the instant either merge side stores it
      as a string for even one row. Gate met — exact file:line cited above in "What I verified".
- [x] [CODE] P1. Fix it so the consolidator persists schema-typed columns (int/bool/float, not utf8), get it into the
      `market-tick-data-service` image, verify via a fresh consolidator cycle reading the written parquet directly. —
      **DONE — already shipped + deployed before this session (no new commit needed).** Fix:
      `unified-trading-library@02fc4661` (2026-07-21, `_TYPED_MANIFEST_COLUMNS` + `_typed_col_projection`,
      anti-regression test `tests/unit/test_manifest_consolidator_numeric_varchar_hardening.py`), hardened further at
      `unified-trading-library@14301571` (2026-07-24, unrelated TOCTOU fix, same file). Redeploy: confirmed live —
      `uts-prod-manifest-consolidator-instruments-sports` execution `...-mlzjz` (started 2026-07-25T22:48:02Z) resolved
      `market-tick-data-service:latest` to `@sha256:bcd89e6...`, built from `market-tick-data-service@b444608`
      (2026-07-25T22:35:18Z) pinning `unified-trading-library@4e696d32` — confirmed that pinned UTL commit already
      contains the fix. No rebuild/redeploy action was needed or taken THIS session — the fleet's standard
      LDR→main→backmerge promotion pipeline had already rebuilt + republished the image (GH Actions `image-build-gate`
      run `30177688365`, SUCCESS, `market-tick-data-service` PR #725, 2026-07-25T22:30:08Z) before this session started;
      `Evidence:` is the LIVE RUNNING EXECUTION's resolved image digest above (stronger than a build-success citation —
      it proves the fix is the code actually executing in prod right now), cross-checked against
      `gcloud artifacts docker images describe .../market-tick-data-service:latest` (digest
      `bcd89e69d2ea3307defaf70ba089c4ea2ed930f586b75318d721d33ea240bf04`, matches). Verification: read
      `_index/availability_index.parquet` directly off BOTH previously-poisoned buckets
      (`instruments-store-sports-prd-central-element-323112`, generation 1785019456171804, written 2026-07-25T22:44:16Z;
      `instruments-store-pred-prd-central-element-323112`, generation 1785019721960244, written 2026-07-25T22:48:41Z) —
      `instrument_count`/`row_count`/`schema_version` = arrow `int64`, `expected_window_completeness_fraction` =
      `double`, `expected`/`available` = `bool`, every non-null Python value confirmed `int`/`bool` (not `str`). Full
      command + output cited above in "What I verified".

## Done definition

A fresh consolidator run on a previously-poisoned bucket (sports or prediction) writes the canonical index with typed
columns, verified by direct parquet read — **MET, verified live on both named buckets 2026-07-25 (see "What I
verified").** No code change was needed this session (the fix already shipped under `unified-trading-library@02fc4661`);
that commit itself shipped `quality-gates.sh`-green via quickmerge.
