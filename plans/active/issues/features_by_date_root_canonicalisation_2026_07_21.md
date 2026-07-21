---
doc_type: issue
title: Features data-at-rest root canonicalisation (2026-07-21) — every features tree MUST carry by_date/day=
summary: >-
  Operator ruling 2026-07-21 ratifies the UTL paths registry — every features data-at-rest tree MUST carry the
  by_date/day= root level. The registry already declares it (delta_one/by_date/day=, onchain/by_date/day=,
  volatility/by_date/day=) but two live writers diverge from their own registry SSOT. The features-cefi delta_one writer
  emits delta_one/day= (no by_date/ level) and the volatility writer writes at BUCKET ROOT (get_data_sink with no
  prefix, so no volatility/by_date/ level at all). Both are NON-CANONICAL and must be repointed to the registry shape.
  onchain and sports already carry by_date/ on their primary writers and need a verify-only alignment pass.
status: open
nature: issue
asset_group: [cefi, defi, sports]
stage: [data]
repos: [features-service, unified-trading-library]
scope: [engineer, admin]
tags: [canonicalisation, features, by-date, data-at-rest, hive, delta-one, volatility, migration, operator-ruling]
related:
  [
    instrument_availability_hive_canonicalisation_2026_07_21.md,
    ../../../codex/02-data/cross-asset-canonical-target-ssot.md,
    ../../../codex/02-data/canonical-cutover-register.md,
    ../../../codex/02-data/non-canonical-path-inventory.md,
    ../../../codex/02-data/feature-formula-versioning.md,
  ]
created: 2026-07-21
last_updated: 2026-07-21
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: operator ruling 2026-07-21 (features data-at-rest root = by_date/day= is the SSOT)
depends_on: []
---

# Features data-at-rest root canonicalisation (2026-07-21)

> **The ruling (operator, 2026-07-21).** The features data-at-rest root is `by_date/day=`, and it is the SSOT. This
> RATIFIES the UTL paths registry, which already declares the `by_date/day=` level for every features kind. Any features
> writer emitting a tree WITHOUT the `by_date/day=` level is NON-CANONICAL and must be fixed to match the registry. The
> registry template is the SSOT — the writer is the surface that must be brought into line, never the other way round.

## What the SSOT already says (grounding, verified 2026-07-21)

The UTL paths registry declares `by_date/day=` for every features kind:

- `unified-trading-library/unified_trading_library/config_interface/paths/registry.py:57` — `delta_one_features`:
  `path_template="delta_one/by_date/day={date}/feature_group={feature_group}/timeframe={timeframe}/"`.
- `registry.py:74` — `onchain_features`: `path_template="onchain/by_date/day={date}/feature_group={feature_group}/"`.
- `registry.py:90` — `volatility_features`:
  `path_template="volatility/by_date/day={date}/feature_group={feature_group}/"`.

Each kind is the folded per-asset-group `features-{category}` bucket with the kind as a top-level object-key PREFIX
(`delta_one/`, `onchain/`, `volatility/`), then `by_date/day=…`. This is the canonical target.

## The two NON-CANONICAL writers (the actual finding)

### 1. features-cefi `delta_one` writer — emits `delta_one/day=` (NO `by_date/` level)

`features-service/features_service/delta_one/app/core/feature_writer.py`:

- `:132-136` — the sink is built as
  `get_data_sink(bucket=self.bucket, prefix="delta_one", routing_key=self.asset_group.lower())`. The prefix is
  `"delta_one"`, NOT `"delta_one/by_date"`.
- `:610-615` — the write partition dict starts at `day=`:
  `{"day": …, "feature_group": …, "feature_group_version": …, "timeframe": …}`. Combined with the `delta_one` prefix
  this emits `delta_one/day={date}/feature_group=…/feature_group_version=…/timeframe=…/{id}.parquet` — **no `by_date/`
  level**, diverging from `registry.py:57`.
- `:793-796` — `check_exists` probes the SAME non-canonical path
  (`f"delta_one/day={…}/feature_group={…}/feature_group_version={…}/timeframe={…}/{id}.parquet"`). This MUST be fixed in
  lockstep with the write path, or the idempotent-skip probe will look at the old location and re-compute + re-write
  every partition forever.

Target: prefix `"delta_one/by_date"` (or equivalent) so the emitted tree is
`delta_one/by_date/day={date}/feature_group=…/feature_group_version=…/timeframe=…/{id}.parquet`, matching the registry.

### 2. volatility writer — writes at BUCKET ROOT (`get_data_sink` with NO `prefix=`)

`features-service/features_service/volatility/core/feature_writer.py`:

- `:152-155` — the sink is built as `get_data_sink(bucket=self.bucket, routing_key=self.asset_group.lower())` with **no
  `prefix=` argument at all**. There is no `volatility/` kind-prefix and no `by_date/` level.
- `:331-335` — the write partition dict is `{"day": …, "feature_group": …, "timeframe": …}`, filename
  `{underlying}.parquet` (`:340`). With an empty sink prefix this emits
  `day={date}/feature_group=…/timeframe=…/{u}.parquet` **at the bucket root**, diverging from `registry.py:90`
  (`volatility/by_date/day=…`).

Target: `prefix="volatility/by_date"` so the tree is
`volatility/by_date/day={date}/feature_group=…/timeframe=…/{u}.parquet`. This is the operator-noted "volatility writer
bucket-root bypass" and is now clearly non-canonical under the ruling.

### 3 & 4. onchain + sports — verify-only alignment (primary writers already canonical)

- **onchain** — `features-service/features_service/onchain/adapters/onchain_writer.py:62` returns
  `by_date/day={date}/feature_group={group}/{protocol}.parquet` under the `onchain/` kind-prefix, i.e. already
  `onchain/by_date/day=…` (matches `registry.py:74`). **Verify** the secondary
  `onchain/engine/feature_observation_writer.py:70` path (`onchain/{data_type}/asset_group=…`, no `by_date/day=`) — it
  is a different tree (`feature_observation_snapshot`) and may or may not be in scope for the `by_date/day=` root;
  confirm before touching.
- **sports** — `features-service/features_service/sports/data/writer.py:26`
  (`DEFAULT_PATH_TEMPLATE = "sports_features/by_date/day={date}/feature_group={feature_group}/"`) already carries
  `by_date/day=`. **Verify** `sports/data/feature_versioning.py:57` (`get_data_sink(bucket=bucket, prefix="by_date")` —
  prefix is `"by_date"`, missing the `sports_features/` kind-prefix) and align it to the full
  `sports_features/by_date/…` shape if it writes real feature data.

## Why this matters (do not descope)

`by_date/day=` is the shard-atom date root the manifest, the honest-coverage harness and every downstream reader key on.
A writer that omits it desyncs the four canonical surfaces (GCS path vs manifest key vs data-status render) for the
folded features buckets. This is a data-at-rest correctness item, not cosmetics.

## Migration note

Existing `delta_one/day=…` (features-cefi) and bucket-root `day=…` (volatility) objects are `migration_pending`: they
were written before this ruling and are the current authoritative copies. Fix the writer FIRST (with `check_exists`/read
paths in lockstep), PROVE it green on a real day, THEN migrate the historical objects UP into the `by_date/day=` tree,
THEN re-sync the manifest / data-status. Do not delete the old tree until the twin is verified present.

## Todos

- [ ] 1. [DATA] P1. Repoint the features-cefi `delta_one` writer sink prefix from `"delta_one"` to `"delta_one/by_date"`
      (`delta_one/app/core/feature_writer.py:132-136`) so the emitted tree matches `registry.py:57`; keep the partition
      dict (`:610-615`) unchanged (day-first is fine once the prefix carries `by_date/`).
- [ ] 2. [DATA] P1. Fix the `delta_one` `check_exists` probe (`:793-796`) in the SAME change so it probes the new
      `delta_one/by_date/day=…` path — otherwise every backfill re-computes + re-writes each partition.
- [ ] 3. [DATA] P1. Add `prefix="volatility/by_date"` to the volatility writer sink
      (`volatility/core/feature_writer.py:152-155`) so it stops writing at bucket root; verify the volatility read /
      idempotent-skip path matches the new prefix in lockstep.
- [ ] 4. [REVIEW] P1. Verify onchain: confirm `onchain/adapters/onchain_writer.py:62` already emits
      `onchain/by_date/day=` (canonical) and decide whether `onchain/engine/feature_observation_writer.py:70`
      (`onchain/{data_type}/asset_group=`) is in scope for the `by_date/day=` root — align it or record it as
      out-of-scope with a reason.
- [ ] 5. [REVIEW] P1. Verify sports: `sports/data/writer.py:26` is already canonical; align
      `sports/data/feature_versioning.py:57` (`prefix="by_date"`) to the full `sports_features/by_date/…` shape if it
      writes feature data, else record why it is exempt.
- [ ] 6. [DATA] P1. PROVE the fixed delta_one + volatility writers green on one real day (features write +
      skip-if-fresh), then migrate historical `delta_one/day=…` and bucket-root `day=…` objects UP into the
      `by_date/day=` tree.
- [ ] 7. [DATA] P1. Re-sync the availability manifest + data-status render for the migrated features cells so all four
      canonical surfaces agree; verify the coverage surface after the migration.
- [ ] 8. [REVIEW] P1. On writer ship, record the features `by_date/day=` cutover date in
      `codex/02-data/canonical-cutover-register.md` (repo@sha), and flip the non-canonical-path-inventory row #17
      disposition to EXECUTED with a dated post-migration probe.
