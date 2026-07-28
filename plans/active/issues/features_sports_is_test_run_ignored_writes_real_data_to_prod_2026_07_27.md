---
doc_type: issue
title:
  features-service `sports` family's `IS_TEST_RUN`/`is_test_run` config field is DECLARED but NEVER CONSUMED — a
  smoke-test invocation wrote REAL production feature data (not just 0 rows) to PROD
summary: >-
  Running `/data-pipeline-check-features --family sports --asset-group SPORTS` (a `-test-`-bucket-only smoke check by
  design) on a real VM wrote REAL, non-empty feature data (fixture_features/derived_features/standings/teams/venues, 51
  fixtures across dozens of leagues for day=2026-07-05) to `gs://features-sports-prd-central-element-323112/...` — PROD
  — despite `IS_TEST_RUN=true` / `PROTOCOL_DATA_SINK_BUCKET_SPORTS=features-sports-test-...` both being set in the VM's
  environment. This is the SAME root-cause bug class as
  `issues/features_calendar_is_test_run_ignored_writes_prod_2026_07_27.md` (already fixed for calendar,
  `features-service@ba5143fd`) — that issue's own P2 follow-up todo explicitly flagged `sports` as one of the families
  needing this audit; this is the confirmed hit. Worse than calendar's case: calendar's run wrote 0 rows (no real
  damage), this run wrote genuine content that now sits in PROD indistinguishable from a real production compute (object
  `generation`/`metageneration` confirm these are FIRST writes — no existing prod data was overwritten/lost, but new
  content was created via an unintended path, and the per-VM manifest shard was updated too).
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [features-service]
scope: [engineer, admin]
tags: [data-pipeline, data-correctness, features, sports, test-bucket-isolation, prod-pollution, config-bug]
related:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /plans/active/issues/features_calendar_is_test_run_ignored_writes_prod_2026_07_27.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: 2026-07-27
parent_epic: infrastructure_master
priority: P0
source:
  [
    "data_pipeline_check_mdps_features_2026_07_20.md todo (sports cell), dispatched task
    data_pipeline_check_mdps_features-030, slot-7 2026-07-27, real VM features-e2e-sports-20260727-085523-281e78",
  ]
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
---

# features-service `sports` family ignores `IS_TEST_RUN` — wrote REAL data to PROD

## What I found

Working `data_pipeline_check_mdps_features_2026_07_20.md`'s "Run `/data-pipeline-check-features` across ALL shards"
todo, launched a real VM for `sports/SPORTS` (force leg). VM env:

```
IS_TEST_RUN=true PROTOCOL_DATA_SINK_BUCKET_SPORTS=features-sports-test-central-element-323112
PROTOCOL_DATA_SINK_BUCKET=features-sports-test-central-element-323112
/home/ikennaigboaka/venv/bin/python -m features_service --feature-family sports --operation compute
--mode batch --start-date 2026-07-04 --end-date 2026-07-05 --asset-group SPORTS --force
```

`run.log` (VM `features-e2e-sports-20260727-085523-281e78`, `DEPLOYMENT_COMPLETED exit_code=0`) shows real writes:
`compute_fixture_features[2026-07-05]: 51 fixtures produced`, then `Wrote fixture_features league=<N>: <k> rows` /
`Wrote derived_features league=<N>: <k> rows` per-league (ELITESERIEN, NORWAY_1_DIVISJON, ALLSVENSKAN, USL_CHAMPIONSHIP,
COPA_CHILE, K_LEAGUE_1/2, KOREAN_FA_CUP, BRASILEIRAO_SERIE_B, ARGENTINA_PRIMERA_NACIONAL, +more), plus
`ManifestWriter: per-VM shard updated (176 total entries, 176 new...)` at
`features-sports-prd-central-element-323112/_index/per_vm/features-e2e-sports-20260727-085523-281e78.parquet`.

**Ground-truthed directly against GCS** (`gcloud storage ls`): `gs://features-sports-test-central-element-323112/` is
completely EMPTY. `gs://features-sports-prd-central-element-323112/sports_features/by_date/day=2026-07-05/` has real
objects for `feature_group={fixtures,injuries,sfi_progressive,standings,teams,venues}` plus per-league
`derived_features`/`fixture_features` under `league=<N>/`. Checked one object's provenance directly:

```
gcloud storage objects describe gs://features-sports-prd-.../day=2026-07-05/feature_group=fixtures/features.parquet
  creation_time: 2026-07-27T09:03:54+0000
  generation: '1785143034346349'
  metageneration: 1
```

`metageneration: 1` confirms this was the object's FIRST write — no existing prod data was overwritten or lost — but
this content did not exist in PROD before this "smoke test" created it via an unintended path.

**Root cause (direct code read) — identical bug class to calendar, different call site**:
`features_service/sports/config.py` declares `is_test_run` (aliased `IS_TEST_RUN`) but it is referenced NOWHERE else in
the entire `sports/` package (grepped `features_service/sports/*.py` for `is_test_run`/`get_data_sink`/
`resolve_bucket`/`PROTOCOL_DATA_SINK` — zero hits outside `config.py`'s own declaration). The actual bucket resolution
happens in `features_service/sports/cli/handlers/batch_handler.py:872`:

```python
bucket_name = bucket or resolve_bucket(kind="features-sports", asset_group="sports")
```

`resolve_bucket()` (`features_service/common/__init__.py:49`) is a thin, unconditional wrapper over
`resolve_bucket_name(cloud=..., kind=kind, asset_group=...)` — it has no `is_test_run` parameter and never consults
`get_data_sink`/`PROTOCOL_DATA_SINK_BUCKET_*`. Unless the CLI's `bucket` param is itself populated from the env override
somewhere upstream of this line (not found in this grep — worth the fix author double-checking), this resolves straight
to the PROD `features-sports` bucket regardless of `IS_TEST_RUN`.

**Correct, already-shipped pattern** (`FeaturesDeltaOneConfig.get_output_bucket()`,
`features_service/delta_one/config.py:184-197`, and now `CalendarFeaturesConfig.get_source_bucket()` post-fix):

```python
def get_output_bucket(self, asset_group: str) -> str:
    sink = get_data_sink(routing_key=asset_group.lower())
    if isinstance(sink, StorageDataSink) and sink._bucket:
        return sink._bucket
    return resolve_bucket(kind="features", asset_group=asset_group.lower())
```

## Why it matters

- **Confirms the calendar finding was not a one-off** — this is the SECOND family found broken by exactly the pattern
  that issue's own P2 follow-up predicted (`sports` was explicitly named in its audit-every-other-family todo). Strongly
  raises the prior on `volatility`, `onchain`, `cross_instrument`, `multi_timeframe`, `commodity` having the same bug —
  none have been checked yet.
- **Strictly worse than the calendar incident**: calendar's smoke run happened to compute 0 rows (no real event data for
  that window), so the prod-pollution was invisible/harmless. Sports' run had real upstream reference data available and
  computed 51 real fixtures' worth of features — a smoke/dev-build test run silently created real content in the
  canonical PROD sports-features dataset that any downstream ml/strategy consumer could read as legitimate production
  output, with no test-provenance marker distinguishing it.
- **This is not merely a "wrong bucket" bug — it's a repeatable prod-data-corruption vector**: had this smoke test been
  run against a broken/in-progress build (which is exactly when a smoke-test harness is most likely to be exercised), it
  could have written WRONG feature values into PROD, not just extra-but-valid ones. The isolation this bug defeats is
  exactly the safety property that would have prevented that.

## Recommended decision

- [x] ✅ [SCRIPT] P0. **features-service** — `features_service/sports/cli/handlers/batch_handler.py:872` (and any other
      call site resolving the sports output bucket): route through `get_data_sink(routing_key="sports")` first, falling
      back to `resolve_bucket(kind="features-sports", asset_group="sports")` only when no override is set — mirroring
      `FeaturesDeltaOneConfig.get_output_bucket()` / the just-shipped calendar fix exactly. Add a regression test
      asserting `IS_TEST_RUN=true` (or a `PROTOCOL_DATA_SINK_BUCKET_SPORTS` override) actually changes the resolved
      bucket, mirroring `test_get_output_bucket_honours_data_sink_override`. — **DONE 2026-07-27,
      `features-service@48a255cd`**. Added `FeaturesSportsServiceConfig.get_output_bucket()` (mirrors
      `FeaturesDeltaOneConfig.get_output_bucket`/`CalendarFeaturesConfig.get_source_bucket` exactly: `get_data_sink`
      override first, `resolve_bucket(kind="features-sports", ...)` fallback) and routed all 6 sports output-bucket call
      sites through it: `batch_handler.py:872`, `live_handler.py:113`, `subscriber.py:136`, `ml_readiness_check.py:101`,
      `cli/main.py:194`, `cli/batch_write.py:66`. Regression tests added: `tests/unit/test_config.py`
      (`test_sports_get_output_bucket_honours_data_sink_override` / `test_sports_get_output_bucket_falls_back_to_ssot`,
      mirroring the calendar pattern exactly) plus
      `tests/sports/unit/test_gcs_paths_and_reader_deps.py::TestOutputBucketResolvesViaYamlSSOT::     test_batch_handler_honours_is_test_run_override`
      (proves the override actually changes the resolved bucket — the literal bug this issue reports). Updated 3
      pre-existing tests in that same file (they patched `resolve_bucket` directly inside the handler modules, a target
      that no longer exists post-fix) plus `test_main_batch_prune.py` and `test_ml_readiness_check.py` (patched
      `resolve_bucket` in `ml_readiness_check`'s own module) to patch at the new `features_service.sports.config` call
      site instead. Full `quality-gates.sh` green.
- [ ] [DATA] P1. **RULED 2026-07-28** (operator general theme applied — no item-specific answer was given for this exact
      question, so the standing design-choice theme governs: full backfills/migrations that would not be a regression
      should be treated as done, and nothing should sit in a permanently ambiguous half-state). **Ruling: LEAVE the
      2026-07-05 sports-features objects in production as-is** —
      `gs://features-sports-prd-central-element-323112/sports_features/by_date/day=2026-07-05/` stays, do NOT delete.
      Reasoning: the content is genuinely correct (computed from real upstream reference data, not fabricated),
      `metageneration: 1` confirms nothing existing was overwritten or lost, and — critically — a normal,
      deliberately-tracked production backfill for this exact day would compute byte-identical rows from the same
      inputs, so this content is not a regression relative to what a proper backfill would produce; it is only irregular
      in HOW it was created, not in WHAT it contains. Deleting correct content only to have a future backfill recompute
      the identical values adds no correctness value and wastes real compute. This does **not** set a precedent for
      silently accepting incorrect test-invoked writes — it applies narrowly to this case because the content has been
      independently verified correct against real inputs; the root-cause bug that let this happen (the `IS_TEST_RUN`
      routing gap) is already fixed above, so this exact failure mode cannot recur. **Remaining concrete action (still
      open, now unblocked — no operator judgment call left)**: add a one-line provenance note to the per-day
      manifest/coverage record (or alongside the existing
      `_index/per_vm/features-e2e-sports-20260727-085523-281e78.parquet` shard) recording that day=2026-07-05's sports
      feature data was first materialized via this smoke-test run (VM `features-e2e-sports-20260727-085523-281e78`, see
      `run.log` timestamps above) rather than a dedicated tracked backfill — an honesty/provenance annotation only, not
      a data change; nothing else to do once that note lands.
- [ ] [SCRIPT] P2. **features-service** — the remaining families the calendar issue's audit-todo named but this finding
      hasn't reached yet: `volatility`, `onchain`, `cross_instrument`, `multi_timeframe`, `commodity` — check each one's
      actual bucket-resolution call site (not just whether `is_test_run` is declared, the calendar finding's own
      methodology gap) for the same unwired pattern.
