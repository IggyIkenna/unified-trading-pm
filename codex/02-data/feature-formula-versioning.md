---
scope: [engineer]
last_reviewed: 2026-05-28
---

# Feature Formula Versioning (delta_one)

> **What it is:** The mechanism by which every parquet file in `features-delta-one-{ag}-{pid}` carries the formula
> version that produced it, and downstream ML / strategy consumers can pin to a specific version. Complements
> [`artifact-versioning.md`](../04-architecture/artifact-versioning.md) § Feature groups by naming the concrete files +
> contracts.

## Why

A calculator's math can change. If we don't tag every emitted row with the version of the formula that produced it, the
GCS corpus becomes a silent mix of "v1 RSI" and "v2 RSI" rows, and any ML model trained on the older data is silently
stale when serving inference on the newer.

Pinning ALSO enables intentional A/B: the same calculator group can ship two formula versions in parallel — `v1`
consumed by the live model, `v2` consumed by a shadow model that's being evaluated for promotion.

## The four files

| File                                                       | Purpose                                                                                                                          |
| ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `features_service/delta_one/app/features/registry.py`      | Declarative SSOT — every emitted column has a `FeatureSpec` with `formula_version: int`, `status`, `priority`, `implementation`. |
| `features_service/delta_one/app/features/formula_hash.py`  | Drift-detection helper — `compute_formula_hash(method)` canonicalises source + sha256.                                           |
| `features_service/delta_one/app/features/status_report.py` | Operator CLI (`features-status`) — summary / detailed / `--check-drift`.                                                         |
| `features_service/delta_one/app/core/feature_writer.py`    | Stamps the version into every parquet at write time.                                                                             |

## Where the version lives: GCS path partition + file-level metadata

Every parquet emitted by `feature_writer._write_parquet` carries the version in **two places**, both small:

1. **GCS hive partition key** — the canonical pin surface. The version is a directory level in the path:

   ```
   gs://features-delta-one-{ag}-{pid}/
     feature_group=technical_indicators/
       feature_group_version=2/            ← partition key
         timeframe=1h/
           day=2024-01-15/
             BTC-USDT.parquet
   ```

   Consumers pinning `@v2` list only `feature_group_version=2/` paths — no parquet bytes opened on the v1 corpus.
   BigQuery external tables, DuckDB, Polars `scan_parquet` with hive_partitioning, Spark, all auto-discover the key and
   expose it as a queryable column for free.

2. **File-level parquet key-value metadata** — three keys in the parquet footer (one entry per file, ~tens of bytes,
   regardless of row count):
   - `feature_group_version` (single int, mirrors the path partition value)
   - `feature_column_versions` (JSON `{column_name: int_version}` for every registered output column in the file)
   - `feature_group` (the group name; survives if the file is moved out of its partition)

   Kept primarily for **drift detection / forensic visibility**: any stray file (copied out of its partition, served via
   a non-hive reader, audit sample) still self-describes. The audit checklist item (l) verifies path ↔ metadata
   agreement — a mismatch flags a writer bug.

Read via PyArrow:

```python
import pyarrow.parquet as pq
pf = pq.ParquetFile("gs://features-delta-one-defi-PID/feature_group=technical_indicators/feature_group_version=2/.../instr.parquet")
meta = pf.metadata.metadata  # dict[bytes, bytes]
print(meta[b"feature_group_version"])      # b'2'
print(meta[b"feature_column_versions"])    # b'{"rsi_14": 2, "macd": 1, ...}'
print(meta[b"feature_group"])              # b'technical_indicators'
```

**There is NO per-row column.** The initial Phase 3 implementation added a constant `feature_group_version: Int32`
sidecar column on every row; operator directive 2026-05-28 reverted that: "we will have millions of files and many rows,
can't we assign this column into the gcs path itself?" — yes, path-partitioning lets selective reads list only matching
paths instead of opening every parquet to filter on a column.

## Group version resolution

The single per-file `feature_group_version` int is:

```python
feature_group_version = max(spec.formula_version for spec in get_specs_by_group(group))
```

Bump ANY column's `formula_version` in the registry → the group's version bumps. Matches codex `artifact-versioning.md`
§ Rule 4 (consumer PIN by `technical_indicators@v2`).

## Bumping a formula version

When you change the math in a calculator's `_calculate_features` method (or any of its helper methods):

1. **Decide scope**: did this change affect ALL columns the calculator emits, or just some? In practice it's usually all
   — that's the simpler case + matches the per-group pin model.
2. **Edit the registry**: bump the `formula_version` field on every affected `FeatureSpec`. Example: market_structure
   swing-detection logic now uses an ATR-percentile gate instead of a flat threshold → bump every
   `FeatureSpec(group="market_structure", ...)` from `formula_version=1` to `formula_version=2`.
3. **Archive the old code (optional)**: rename the prior method to `_calculate_features_v1` if the old logic must be
   reproducible. Future-you will thank present-you.
4. **Commit** with `feat!` (semver-major). The breaking-ness is in the consumer pin: any strategy/ML config pinning
   `@v1` will continue to read v1-tagged GCS data, but new emissions tag as v2. The "break" is when an `@v1` consumer
   needs new data and finds only v2 — that's the consumer-opt-in upgrade window.
5. **Verify** via `features-status --group <group>` that the bump landed (group_version column shows `v2`) and
   `features-status --check-drift` prints the new method's hash.

**What NOT to bump on**:

- Config changes (window size, threshold value) → those are at the consumer-config layer, not the formula layer.
  Operator directive 2026-05-28: "rsi 14 vs rsi 18, that is config change."
- Comment / docstring / type-hint edits → the canonicaliser in `formula_hash._canonicalise` strips these.

## The 0 sentinel

`feature_group_version=0` is reserved for groups with **no registered FeatureSpecs**. The writer falls back to the 0
partition + logs a warning rather than raising — refusing to write would brick existing batch handlers. The sentinel
appears visibly in the GCS path (`feature_group_version=0/`) so the gap is operationally obvious without parsing
per-file metadata.

Today every group in `CALCULATOR_REGISTRY` has at least one spec (Phase 2 catalogued all 34), so the sentinel SHOULD
only appear:

- on un-migrated parquets written **before** this Phase landed (those live at the pre-correction path with no
  `feature_group_version=` segment at all — readers handle that as "legacy / unknown"),
- transiently if a new calculator class is added without its registry entry yet (audit item (i) catches this; lifetime
  should be minutes, not days).

Strategies opting into the versioning contract MUST require `>=1`.

## Drift detection

`features-status --check-drift` computes the SHA-256 of every calculator's `_calculate_features` method (canonicalised:
comments, docstrings, blank lines stripped) and prints the baseline. A future phase wires this into `quality-gates.sh`:

1. The first time a calculator's method is baselined, record the hash on the corresponding `FeatureSpec.formula_hash`
   field.
2. On every commit, recompute. If a hash changed without the `formula_version` bumping → fail the gate. Either revert
   the math edit, or bump the version.

This catches the most common Phase 3+ regression: edit the math, forget to bump, GCS silently gets
v1-tagged-but-v2-formula rows. The drift gate makes that operationally impossible to merge.

## Status field

Every `FeatureSpec` declares a
`status: Literal["verified", "tested", "in_dev", "listed", "blocked", "deprecated", "need_data"]`. Semantics:

| Status       | Meaning                                                                        |
| ------------ | ------------------------------------------------------------------------------ |
| `verified`   | Passes 2.2 ta-lib equality OR formula independently audited; production-ready  |
| `tested`     | Passes 2.4 / 2.6 / 2.7 structural + distribution invariants                    |
| `in_dev`     | Being actively iterated on; do NOT consume from prod ML                        |
| `listed`     | Calculator exists, registry entry exists, but no automated verification yet    |
| `blocked`    | Known wrong / dependency missing; named successor required                     |
| `deprecated` | Superseded; archive the function as `_v{N}` and bump formula_version           |
| `need_data`  | Formula correct but downstream data not yet available (e.g. awaiting backfill) |

2.4 / 2.6 / 2.7 are parametrized only over specs with `status in {"verified", "tested"}` — the `"listed"` placeholders
(Phase 2 mass-catalogue) are documented-but-unverified by design. Promote a spec from `"listed"` → `"tested"` once
you've hand-audited the formula AND the 2.4/2.6/2.7 invariants are passing.

## Consumer pin pattern (target — not yet shipped on strategy side)

```yaml
# strategy_config.yaml — target shape, post-this-plan
feature_group_refs:
  - delta_one/technical_indicators@v2 # bumped formula
  - delta_one/market_structure@v1 # unchanged
  - delta_one/wedge_quality@v1
  - delta_one/momentum@v1
```

The strategy / ML training service reads only files whose `feature_group_version` matches the pin. Mixed-version reads
are explicitly rejected unless the config opts in with `accept_any: true` (for ad-hoc analysis, not production).

## Composes with

- `codex/04-architecture/artifact-versioning.md` — the 3-axis versioning model (code / artifact / schema). This doc is
  the per-features-service implementation of the Artifact axis for the `feature_group` artifact type.
- `codex/02-data/availability-manifest-and-data-status.md` — the manifest row key extension to carry
  `feature_group_version` is deferred (cross- repo, separate plan).
- `codex/06-coding-standards/strategy-identity-versioning.md` — strategy configs reference
  `feature_group_versions: [...]` as part of the version tuple emitted on every event.

## Plan + history

Shipped in `plans/active/features_registry_status_versioning_2026_05_28.md` across 5 phases:

- Phase 1: FeatureSpec schema extension (status/priority/formula_version/implementation)
- Phase 2: 47 → 1,382 specs (catalogued 29 missing groups)
- Phase 3: per-group version stamped into parquet (sidecar + file-level metadata)
- Phase 4: features-status CLI + drift baseline
- Phase 5: this doc + codex alignment
