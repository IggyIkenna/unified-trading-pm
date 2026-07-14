---
doc_type: issue
title:
  Sports derived_features/fixture_features are (and always were) per-league numeric-id partitions — ml-service training
  loader reads ONLY the day-level atom, so derived_features silently never loads into the ML matrix; plus manifest
  failure-atom (day-level) vs success-atom (per-league) mismatch leaves stale attempted_failed rows
summary:
  "Diagnosis of the 2026-07-14 GW features recompute (fss-backfill-vm-1/2/3) 'wrong shape' suspicion: NOT a defect of
  the recompute. The per-league shape sports_features/by_date/day=<D>/league=<raw_af_id>/feature_group={derived,fixture}
  _features/features.parquet is the writer's canonical behaviour since the 2026-05-08 subtree import and matches ALL
  bucket history (2021/2022/2023/2024 probes) — a day-level derived_features/fixture_features parquet has NEVER existed
  in any era. The named gates are unaffected: check_pipeline_completeness.py is manifest-driven (no GCS path reads) and
  verify_ml_readiness.py/ml_readiness_check.py reads odds_features only (day-level, unchanged). REAL finding #1
  (cross-repo, data-correctness): ml-service SportsFeatureLoaderMixin._load_sports_group_parquet
  (ml_service/training/app/core/sports_feature_loader.py:43) downloads only the exact day-level blob
  feature_group={group}/features.parquet, and derived_features is in SPORTS_FEATURE_GROUPS (feature_query_support.py:76)
  — so the 559-column primary ML feature source can never load from GCS; training proceeds on odds/entity-state only.
  REAL finding #2 (features-service, minor): _run_feature_group's record_failed uses row_key {date, feature_group,
  data_type} WITHOUT league_id while successes are recorded per-league, so 27 stale attempted_failed(ValueError,
  league_id='') rows from the pre-fix 06-27/06-29 waves coexist with today's captured per-league rows for the same
  dates. No relaunch/redo of the recompute is needed (redo cost 0)."
status: open
nature: issue
asset_group: [sports]
stage: [data, features]
repos: [ml-service, features-service]
scope: [engineer]
tags: [sports, features, manifest, data-correctness, ml-training, shard-atom, canonicalisation]
related:
  [
    plans/active/sports_p2_features_history_to_ml_ready_2026_06_27.md,
    plans/active/issues/sports_gw_enrichment_false_empty_manifest_and_dropped_rows_2026_07_14.md,
    codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-14
parent_epic: features_and_ml_master
assigned_vm: NA
execution_scope: local-only
priority: P1
source: [diagnosis agent 2026-07-14 (autonomous loop dispatched off the GW recompute per-league-shape suspicion)]
resolved_by:
locked_by:
estimate_class: infra
estimate_baseline_ai_days: 0.75
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
---

# Sports derived/fixture per-league layout — recompute shape is CANONICAL; the gap is the ml-service day-level-only reader

> **NOTIFY-OPERATOR (cross-repo data-correctness finding).** The 2026-07-14 recompute did NOT write a divergent shape —
> per-league with raw numeric api-football ids IS the historical, writer-canonical layout for `derived_features` +
> `fixture_features` (odds_features is day-level). The defect is on the READ side in ml-service: the training loader
> only probes the day-level blob, so `derived_features` (the 559-column primary ML feature source) has NEVER been
> loadable from GCS by ml-service. No recompute redo is needed.

## Evidence (file:line / bucket)

**Writer path (per-league is normal, both today and for the P2c fleet):**

- `features-service/features_service/sports/data/writer.py:26-27` — `DEFAULT_PATH_TEMPLATE` (day-level) +
  `LEAGUE_PATH_TEMPLATE` (`league={league_id}` inserted when `league_id` non-empty; applied at `writer.py:307-311`).
  Present since the subtree import `features-service@b144552d` (2026-05-08) — predates today's fixes
  (`e2e-testing@b6b04b8`, `deployment-service@a79fa65`), which only touched `--force` forwarding, not the write path.
- `features-service/features_service/sports/cli/handlers/batch_handler.py:530` — ALL three feature groups route through
  `_write_per_league`; `batch_handler.py:309-323` groups by the df's `league_id` column and writes one parquet per
  league, keeping the RAW value in the GCS path by design ("so existing parquets are addressable",
  `batch_handler.py:310-312`) while the manifest key uses the canonical UAC league id via `_canonical_league_id`
  (`batch_handler.py:91-110`). odds_features' exporter df carries no `league_id` column → single day-level parquet
  (`batch_handler.py:300-305`).
- Bucket history: `day=2021-03-06/league=39/feature_group=fixture_features/` (P2c fleet output);
  `day=2022-10-15|2023-04-22|2024-02-10/league=<id>/feature_group=derived_features/features.parquet` all per-league;
  day-level `feature_group=derived_features/` matched **no objects** on 2022-10-15, 2024-02-10, 2025-09-01 probes — the
  day-level atom for these two groups has never existed.

**Consumers:**

- `features-service/scripts/sports/check_pipeline_completeness.py:390-398` — reads `availability_index.parquet`
  (manifest) only; no GCS feature-path reads. Shape-agnostic. UNAFFECTED.
- `features-service/features_service/sports/compute/ml_readiness_check.py:40` — single template
  `.../feature_group=odds_features/features.parquet`; the ML-readiness gate measures the odds matrix only. UNAFFECTED by
  derived/fixture layout.
- `ml-service/ml_service/training/app/core/sports_feature_loader.py:43` — **THE GAP**:
  `sports_features/by_date/day={date}/feature_group={group}/features.parquet` exact-blob download, no `league=` probe;
  `feature_query_support.py:65-77` includes `derived_features` in `SPORTS_FEATURE_GROUPS` ("Primary ML feature source —
  derived cross-calculator features (559 columns)"). Result: `_query_sports_features` silently gets None for
  derived_features on every date, and the horizon-schema sidecar read (`sports_feature_loader.py:68`) misses too.
  `rg 'league=' ml_service/` (excl. tests) = 0 hits — no league-aware read anywhere in ml-service.

**Naming/SSOT check:**

- `codex/02-data/defi-canonical-naming-ssot.md` — DeFi vocabulary only (confirmed via title/summary); does not govern
  this bucket.
- `codex/02-data/sports-gcs-path-ssot.md` + UAC `canonical/domain/sports/gcs_paths.py` — governs the IS
  `sports_reference/` bucket, not `sports_features/`. There is NO codex SSOT for the features bucket layout; the SSOT is
  the writer (`writer.py` docstring cites the legacy `sports-schema-paths.md` format). Raw numeric af-ids in `league=`
  path keys are deliberate writer behaviour; canonical NAMES live in the manifest key. The "numeric ids cleaned from the
  IS index this week" work applies to the IS `sports_reference` index, not features paths. Numeric path keys here are
  therefore NOT a rule violation today — but they are un-canonical and worth migrating only as part of a deliberate
  features-path SSOT (do NOT rename in place; every historical day uses raw ids).

**Fleet completion + manifest (2026-07-14 recompute, window 2025-09-01→11-30):**

- All 3 VMs `VM EXIT rc=0` (vm-1 19:04:09Z / vm-2 19:05:12Z / vm-3 19:03:52Z; 30+30+31=91 dates), self-deleted;
  window-end `day=2025-11-30/league=140/feature_group=derived_features/features.parquet` created 19:03:37Z.
- Manifest (`_index/availability_index.parquet`, read 20:03Z): window rows DERIVED_FEATURES 1,672 captured / 14
  attempted_failed; FIXTURE_FEATURES 1,672 captured / 13 attempted_failed; ODDS_FEATURES 91 captured (day-level). Shard
  atom recorded =
  `(date, feature_group, data_type, league_id=<canonical NAME>, pipeline_mode=batch_footystats| batch_api_football)` —
  76 distinct league_ids, **0 numeric** (thanks to `_canonical_league_id`). 91/91 days have captured derived rows;
  1,626/1,672 derived captured rows re-stamped ≥17:00Z today (rest from the concurrent P2a fleet/earlier waves).
- The 27 attempted_failed rows all have `league_id=''` (day-level atom) and `attempted_at` 2026-06-27→29 — STALE
  pre-fix-wave failures never superseded because `record_failed` (`batch_handler.py:583-588`) omits `league_id` while
  successes are per-league. 12 dates carry both a stale day-level failed row and fresh per-league captured rows.

## Todos

- [ ] [CODE] P1. **ml-service: make the sports GCS loader layout-aware** — in
      `_load_sports_group_parquet`/`_collect_sports_frames_by_date`, when the day-level blob is absent, list
      `sports_features/by_date/day={date}/league=*/feature_group={group}/features.parquet` (single prefix list per
      (date, group), concat league frames; same for `horizon_schema.json` sidecar — any one league's sidecar suffices,
      they're identical projections of the registry). Gate: an ml-service integration test proving derived_features
      loads for a per-league-layout date; training run log shows derived columns in the matrix.
- [ ] [CODE] P2. **features-service: align the failure atom with the success atom** — `record_failed` in
      `_run_feature_group` should carry the same league granularity as `_write_per_league` successes (or a documented
      day-level sentinel that data-status readers treat as superseded when per-league captured rows exist for the same
      (date, feature_group)). Then clean the 27 stale `attempted_failed(ValueError, league_id='')` window rows
      (restamp/supersede), so the window manifest is failure-free.
- [ ] [DOC] P3. **Write the features-bucket path SSOT** (codex/02-data) documenting: odds day-level; derived/fixture
      per-league with RAW af-id keys (historical, addressable); manifest key = canonical league NAME; readers must
      handle both layouts. Cite `writer.py:26-27` + `batch_handler.py:300-323`.

## Non-actions (explicit)

- **No recompute relaunch / no redo** — today's output is byte-shape-identical to all history; redo cost 0.
- **No in-place GCS rename of numeric league dirs** — would orphan every historical reader/manifest reference.
