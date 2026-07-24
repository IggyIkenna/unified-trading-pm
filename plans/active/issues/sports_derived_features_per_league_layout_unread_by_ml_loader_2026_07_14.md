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
status: resolved
nature: issue
asset_group: [sports]
stage: [data, features]
repos: [ml-service, features-service]
scope: [engineer]
tags: [sports, features, manifest, data-correctness, ml-training, shard-atom, canonicalisation]
related:
  [
    plans/archive/2026_07/sports_p2_features_history_to_ml_ready_2026_06_27.md,
    plans/active/issues/sports_gw_enrichment_false_empty_manifest_and_dropped_rows_2026_07_14.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-14
parent_epic: features_and_ml_master
assigned_vm: NA
execution_scope: local-only
priority: P1
source: [diagnosis agent 2026-07-14 (autonomous loop dispatched off the GW recompute per-league-shape suspicion)]
locked_by:
estimate_class: infra
estimate_baseline_ai_days: 0.75
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
resolved_by: ["ml-service@360da40", "features-service@4f83f8db", "features-service@76f234ce", "ml-service@5ee0a8e"]
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

- `/codex/02-data/defi-canonical-naming-ssot.md` — DeFi vocabulary only (confirmed via title/summary); does not govern
  this bucket.
- `/codex/02-data/sports-gcs-path-ssot.md` + UAC `canonical/domain/sports/gcs_paths.py` — governs the IS
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

- [x] [CODE] P1. **ml-service: make the sports GCS loader layout-aware** — in
      `_load_sports_group_parquet`/`_collect_sports_frames_by_date`, when the day-level blob is absent, list
      `sports_features/by_date/day={date}/league=*/feature_group={group}/features.parquet` (single prefix list per
      (date, group), concat league frames; same for `horizon_schema.json` sidecar — any one league's sidecar suffices,
      they're identical projections of the registry). Gate: an ml-service integration test proving derived_features
      loads for a per-league-layout date; training run log shows derived columns in the matrix. —
      **ml-service@360da40** + evidence: 8 loader unit tests (`tests/training/unit/test_sports_feature_loader.py`:
      day-level-only, per-league- only concat, both-present union, empty day, sibling-group filter, per-league sidecar
      fallback) green in `quality-gates.sh --no-fix` exit 0; REAL-bucket runtime verify day=2025-10-20: derived_features
      **(24 fixtures × 728 cols, 17 leagues incl. 39/140)**, fixture_features (24×29), odds_features day-level (31×143)
      unregressed, horizon sidecar 876 cols via per-league fallback, full `_query_sports_features` (24×728). **Second
      read-side gap found + fixed in the same commit**: `Settings.get_sports_bucket()` resolved the legacy FLAT bucket
      `features-sports-{pid}` (near-empty — only `day=2020-01-01` exists there); the writer's real corpus is env-tiered
      `features-sports-prd-{pid}` (cloud-providers.yaml kind=`features-sports`). Now resolves via UTL
      `get_bucket_name("features_sports")` with the template kept as an explicit override escape hatch (mirrors
      ml-service@32f5c94). So pre-fix, ml-service read the wrong bucket AND the wrong layout.
- [x] [CODE] P2. **features-service: align the failure atom with the success atom** — `record_failed` in
      `_run_feature_group` should carry the same league granularity as `_write_per_league` successes (or a documented
      day-level sentinel that data-status readers treat as superseded when per-league captured rows exist for the same
      (date, feature_group)). Then clean the 27 stale `attempted_failed(ValueError, league_id='')` window rows
      (restamp/supersede), so the window manifest is failure-free. — **features-service@4f83f8db + @76f234ce** +
      evidence: **Decision (both halves of the "or")**: (a) when the run has an explicit `league_ids` scope,
      `record_failed` now records one attempted_failed per CANONICAL league — the exact success/expected_unattempted
      atom, so the consolidator's captured-outranks + latest-attempted_at dedup supersedes it naturally on retry
      (proof-of-mechanism: the 06-27 wave's day-level odds_features failure self-healed precisely because odds success
      atoms share the day-level key); (b) WITHOUT a filter the day-level atom is retained DELIBERATELY and documented
      in-code — the league dimension is a property of the output df, which does not exist when the compute raises;
      enumerating a hypothetical league universe would fabricate un-supersedable failed rows for leagues that
      legitimately produce no output. 2 unit tests (per-league atoms under filter / day-level without). **Cleanup
      mechanism (recorded per the manifest rules)**: evidence-gated DELETION via one-off
      `scripts/sports/purge_stale_daylevel_failed_rows_2026_07_14.py` (dry-run default; snapshot/backup-then-write;
      predicate = attempted_failed + blank league_id + derived/fixture + >=1 per-league captured twin with NEWER
      attempted_at, i.e. superseded-in-fact; applied to consolidated index AND `_index/per_vm/*` shards). **Counts**: 28
      consolidated rows (the 27 window rows + one same-class out-of-window row 2026-05-13 fixture_features
      LookaheadBiasError, failed→captured 5s apart) + 2 `_legacy_seed.parquet` shard rows. **Verified across a fresh
      consolidator cycle** (index rebuilt 21:35:42Z post-apply): 0 day-level attempted_failed derived/fixture rows
      corpus-wide; window = DERIVED 1,672 captured / FIXTURE 1,672 captured / ODDS 91 captured, **0 attempted_failed —
      failure-free**. **Hard-learned during apply**: a backup written inside `_index/per_vm/` with a `.parquet` suffix
      IS a shard to the consolidator fan-in (no `.bak` exclusion in `_read_and_merge_per_vm_shards`) — the first apply
      resurrected the 2 seed rows from its own backup; fixed by relocating backups to `_index/purge_backups/`
      (features-service@76f234ce). ⚠️ The instruments-service precedent `scripts/delete_phantom_rows_from_shards.py`
      carries the SAME hazard (`_backup_path` writes `.bak.parquet` next to the shard under `_index/per_vm/`) —
      annotated here per findings-triage (fits instruments-service scope; do not fix from this plan).
- [ ] [DOC] P3. **Write the features-bucket path SSOT** (codex/02-data) documenting: odds day-level; derived/fixture
      per-league with RAW af-id keys (historical, addressable); manifest key = canonical league NAME; readers must
      handle both layouts. Cite `writer.py:26-27` + `batch_handler.py:300-323`.
- [x] [CODE] P2. **ml-service: odds_features cannot join the fixture matrix — join-key mismatch** (found during the P1
      real-bucket runtime verify, 2026-07-14): the real `odds_features` parquet keys rows on **`event_id`** (columns:
      `event_id, home_implied_prob, …`), but `_merge_sports_groups_for_date`
      (`ml_service/training/app/core/sports_feature_loader.py`) requires a **`fixture_id`** column and skips the group
      with a warning ("Sports group 'odds_features' … has no fixture_id column") — so odds features load from GCS but
      never enter the merged matrix. Pre-existing (independent of the layout fix; visible now that loading works). Needs
      an event_id↔fixture_id mapping decision (features-service exporter emits fixture_id? or ml-service maps via the
      fixtures reference?) — cross-repo, decide atom on the features-service side first. — **ml-service@5ee0a8e** +
      evidence: **ROOT SEMANTICS (real day=2025-10-20 parquets)**: odds `event_id` = the RAW the-odds-api event id
      (32-hex, e.g. `6a16dc29e606…`) — MDPS `bucket_assignment_adapter.py:187-188` renames raw ODDS_API
      `event_id`→`fixture_id` and the FSS odds exporter (`_pivot_bucketed_to_fixture`) pivots it back out as `event_id`;
      derived/fixture `fixture_id` = af numeric id (`1390899`) — **ZERO value overlap, NOT a same-value rename**; no
      crosswalk column exists in ANY features/fixtures frame (the odds parquet carries no team/kickoff/league metadata —
      dropped at `compute_odds_batch`). **Decision (read-side, deterministic, never fuzzy)**: merge-time 3-hop crosswalk
      in the loader, exact-equality joins only — (1) MDPS bucketed shards for the same day (the ONLY holder of hex id +
      od team spellings; canonical `pipeline_mode=` prefix probed first, legacy fallback, mirrors FSS
      `read_bucketed_odds`) → (2) IS `sports_reference/mappings/odds_api_team_mapping.parquet`
      (`od_team_name → af_team_id`; the table behind UAC `mapping_resolver`) → (3) sibling same-date loaded frame
      (`home_team_id`+`away_team_id` → `fixture_id`; derived/fixture frames carry all three). Unmapped/ambiguous events
      DROPPED with logged count — honest absence. features-service exporter atom UNCHANGED (no recompute; all historical
      odds parquets stay readable). 7 new unit tests (`TestOddsJoinKeyCrosswalk`:
      attach/unmapped-drop/float-id-normalize/ambiguous-drop/empty-ref-passthrough/ end-to-end-merge/odds-only-no-reads)
      green in `quality-gates.sh --no-fix` exit 0. **REAL-bucket runtime verify day=2025-10-20**: merged matrix **24
      fixtures × 870 cols (was 24×728 — odds' 142 cols now join)**; odds coverage on **13/24 fixtures** = the exact
      deterministically-mappable set (`home/draw/away_implied_prob`, `market_vig`, `best_odds_home` each 13 non-NULL;
      sparse `clv_home` 4); 30/31 odds rows mapped, kept row per fixture = T-24h (pre-existing keep="first" dedup
      semantics unchanged).
- [ ] [DATA] P3. **instruments-service: odds_api_team_mapping coverage gap** (found during the P2 fix, 2026-07-14): the
      IS crosswalk `sports_reference/mappings/odds_api_team_mapping.parquet` (658 rows) has no row for `Burgos CF`
      (SEGUNDA_DIVISION) — the sole unmappable odds event on 2025-10-20 (event `81fcdc22656530bb4daca2deb3f1845f`,
      Burgos CF vs Córdoba). Smaller-league od spellings are likely under-covered; audit mapping coverage against the
      distinct od team names in MDPS bucketed odds and extend the table (IS owns reference data). Until then those
      fixtures' odds rows drop at merge time (honest absence, logged).

## Non-actions (explicit)

- **No recompute relaunch / no redo** — today's output is byte-shape-identical to all history; redo cost 0.
- **No in-place GCS rename of numeric league dirs** — would orphan every historical reader/manifest reference.

## RE-TRIAGE (2026-07-23)

**Verdict: RESOLVED BY LATER WORK.** All 3 P1/P2 `[CODE]` todos are already checked `[x]` in this doc with strong
first-party evidence (unit tests + real-bucket runtime verification against `day=2025-10-20`), so this is a confirmation
pass, not a re-diagnosis:

- ml-service's sports GCS loader is layout-aware (`ml-service@360da40`) — derived_features/fixture_features now load
  from the per-league layout, plus the bucket-resolution bug (flat `features-sports-{pid}` → tiered
  `features-sports-prd-{pid}`) fixed in the same commit.
- features-service's failure-atom/success-atom league-granularity mismatch fixed + 28 consolidated + 2
  `_legacy_seed.parquet` stale rows cleaned (`features-service@4f83f8db` + `@76f234ce`).
- The odds_features↔fixture join-key crosswalk (`event_id`↔`fixture_id`, zero raw-value overlap) fixed via a
  deterministic 3-hop merge-time crosswalk (`ml-service@5ee0a8e`).

Checked whether the two remaining `[ ]` P3 todos have since been done — they have NOT:

- **`[DOC] P3` features-bucket path SSOT** — `find codex/02-data -iname '*sports*'` finds no doc matching this scope
  (`sports-gcs-path-ssot.md` governs the IS `sports_reference/` bucket, not `sports_features/`, as this doc itself
  already notes); `sports_consolidated_closeout_2026_07_19.md`'s sweep (item **I**) still lists this as outstanding.
  Genuinely still open.
- **`[DATA] P3` `odds_api_team_mapping` coverage gap (Burgos CF etc.)** — grepped `plans/active/` for follow-ups; only
  this doc and `sports_p2_features_history_to_ml_ready_2026_06_27.md` reference it, no fix/extension found. Genuinely
  still open.

Flipping `status` to `resolved` (the doc's core cross-repo data-correctness findings are shipped + verified) while
leaving both P3 todos unchecked — this mirrors the convention used elsewhere in this sweep
(`mtds_sports_api_football_wrong_source_reaccumulated_post_wipe_2026_07_22.md`) where `resolved` tolerates a residual,
lower-priority open tail rather than requiring 100% todo completion.
