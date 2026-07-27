---
doc_type: issue
title:
  features-service `calendar` family's `IS_TEST_RUN`/`is_test_run` config field is DECLARED but NEVER CONSUMED — every
  calendar batch write goes to the PROD bucket regardless of test-mode
summary: >-
  Running `/data-pipeline-check-features --family calendar` (a `-test-`-bucket-only smoke check by design) on a real VM
  logged writes to `gs://features-calendar-prd-central-element-323112/...` — the PROD calendar-features bucket — despite
  `IS_TEST_RUN=true` / `PROTOCOL_DATA_SINK_BUCKET=features-calendar-test-...` both being set in the VM's environment.
  Direct code read confirms `is_test_run`/`IS_TEST_RUN` is declared in `CalendarFeaturesConfig` but referenced NOWHERE
  ELSE in the entire `calendar/` package — `get_source_bucket()` unconditionally calls
  `resolve_bucket(kind="features-calendar")` with no test-mode branch and no `get_data_sink(routing_key=...)` override
  lookup, unlike every other feature family (`delta_one` is the documented-correct pattern). This run wrote 0 rows (no
  real damage this time), but the SAME code path would silently write REAL rows to PROD on any day with actual economic
  events — a genuine production-data-pollution risk, not a cosmetic bug.
status: open
nature: issue
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos: [features-service]
scope: [engineer, admin]
tags: [data-pipeline, data-correctness, features, calendar, test-bucket-isolation, prod-pollution-risk, config-bug]
related:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    ../../../cursor-configs/skills/data-pipeline-check-features/SKILL.md,
  ]
created: 2026-07-27
parent_epic: infrastructure_master
priority: P0
source:
  [
    "data_pipeline_check_mdps_features_2026_07_20.md todo (calendar cell), dispatched task
    data_pipeline_check_mdps_features-030, slot-7 2026-07-27, real VM features-e2e-global-20260727-074139-a9e7df",
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

# features-service `calendar` family ignores `IS_TEST_RUN` — writes to PROD unconditionally

## What I found

Working `data_pipeline_check_mdps_features_2026_07_20.md`'s "Run `/data-pipeline-check-features` across ALL shards"
todo, launched a real VM for the `calendar` family (the SKILL.md's own contract: "Writes are **test-bucket-only** —
production features are never mutated"):

```
IS_TEST_RUN=true PROTOCOL_DATA_SINK_BUCKET_GLOBAL=features-calendar-test-central-element-323112
PROTOCOL_DATA_SINK_BUCKET=features-calendar-test-central-element-323112
/home/ikennaigboaka/venv/bin/python -m features_service --feature-family calendar --operation compute
--mode batch --start-date 2026-07-04 --end-date 2026-07-05
```

`run.log` (VM `features-e2e-global-20260727-074139-a9e7df`, `DEPLOYMENT_COMPLETED exit_code=0`) shows:

```
[1/2] 2026-07-04 [time_features]: 0 rows written to gs://features-calendar-prd-central-element-323112/calendar/time_features/by_date/day=2026-07-04/features.parquet
[1/2] 2026-07-04 [economic_events]: 0 rows written to gs://features-calendar-prd-central-element-323112/calendar/economic_events/by_date/day=2026-07-04/features.parquet
[2/2] 2026-07-05 [time_features]: 0 rows written to gs://features-calendar-prd-central-element-323112/calendar/time_features/by_date/day=2026-07-05/features.parquet
[2/2] 2026-07-05 [economic_events]: 0 rows written to gs://features-calendar-prd-central-element-323112/calendar/economic_events/by_date/day=2026-07-05/features.parquet
```

**`-prd-`, not `-test-`** — the env-var test-routing was silently ignored.

**Root cause (direct code read)**: `features_service/calendar/config.py`:

```python
is_test_run: bool = Field(
    default=False,
    validation_alias=AliasChoices("IS_TEST_RUN"),
    description="Route writes to -test- bucket instead of prod (E2E test mode)",
)
...
def get_source_bucket(self) -> str:
    """Get the calendar-features GCS bucket (shared, no asset_group suffix)."""
    return resolve_bucket(kind="features-calendar")
```

`is_test_run` is read from the `IS_TEST_RUN` env var (pydantic `validation_alias`) but **grepped the entire `calendar/`
package — it is referenced NOWHERE ELSE**. `get_source_bucket()` calls `resolve_bucket(kind= "features-calendar")`
unconditionally — no test-mode branch, no `PROTOCOL_DATA_SINK_BUCKET` override lookup at all. `resolve_bucket()` itself
(`features_service/common/__init__.py:49`) has no `is_test_run` parameter — it's a thin wrapper over
`resolve_bucket_name(cloud=..., kind=kind, asset_group=...)`, always resolving to whatever `kind="features-calendar"`
maps to in the SSOT (apparently the PROD name).

**Contrast with the correct, documented pattern** (`features_service/delta_one/config.py:184-197`, `get_output_bucket`):

```python
def get_output_bucket(self, asset_group: str) -> str:
    """... Mirrors feature_writer._get_sink_bucket: honour the UCI PROTOCOL_DATA_SINK_BUCKET_{AG}
    override first, then fall back to the bucket-name SSOT. Without this, the failure path
    ... ignored the SINK override and polluted the canonical features bucket with test
    record_failed rows (issue: features_service_failed_manifest_bucket_override_2026_06_01)."""
    sink = get_data_sink(routing_key=asset_group.lower())
    if isinstance(sink, StorageDataSink) and sink._bucket:
        return sink._bucket
    return resolve_bucket(kind="features", asset_group=asset_group.lower())
```

**This is the SAME failure class as `features_service_failed_manifest_bucket_override_2026_06_01`** (referenced in
delta_one's own docstring) — a write path that bypasses the `get_data_sink`/`PROTOCOL_DATA_SINK_BUCKET` override and
silently lands on PROD — except that incident was scoped to ONE failure-recording path on ONE family; this bug affects
**every single calendar write, unconditionally**, because `calendar/config.py` never wired up the override mechanism AT
ALL, not even for the success path.

## Why it matters

- **Real production-data-pollution risk**: this run's 0-row writes did no visible damage, but the identical code path on
  a day with real economic events would write REAL feature rows to `features-calendar-prd-...` from a test/smoke
  invocation — silently corrupting the canonical calendar-features dataset every downstream ml/strategy consumer reads
  (`economic_events` feeds ml tradfi-optional per the SKILL.md's own "Consumed (safe)" list).
- **The `-test-`-bucket-only guarantee this whole skill (and presumably every other test/smoke harness that exercises
  calendar) depends on is FALSE for this one family** — anyone who trusted the SKILL.md's "Writes are test-bucket-only —
  production features are never mutated" claim for calendar specifically was wrong to.
- Any PAST invocation of `/data-pipeline-check-features --family calendar` (or any other test harness exercising this
  code path) may already have written test artifacts into the PROD calendar bucket — worth a follow-up audit of
  `gs://features-calendar-prd-central-element-323112/calendar/{time_features,economic_events}/` for anomalous zero-row
  or clearly-test-shaped `features.parquet` objects (out of scope for THIS todo, flagged as its own follow-up below).

## Recommended decision

- [x] ✅ [SCRIPT] P0. **features-service** — `features_service/calendar/config.py`: wire `get_source_bucket()` (or add a
      new `get_sink_bucket()`, matching delta_one's naming) to honour `PROTOCOL_DATA_SINK_BUCKET`/
      `PROTOCOL_DATA_SINK_BUCKET_GLOBAL` via `get_data_sink(routing_key=...)` FIRST, falling back to
      `resolve_bucket(kind="features-calendar")` only when no override is set — mirroring
      `FeaturesDeltaOneConfig.get_output_bucket()` exactly. Determine the correct `routing_key` for a GLOBAL
      (non-asset-group) family (likely `"global"` or `"calendar"` — check what `get_data_sink` accepts / how the
      launcher's `PROTOCOL_DATA_SINK_BUCKET_GLOBAL` env var name is derived, to route them consistently). Add a
      regression test asserting `IS_TEST_RUN=true` (or a `PROTOCOL_DATA_SINK_BUCKET` override) actually changes the
      resolved bucket — the exact class of test the June 2026-06-01 incident's fix presumably added for delta_one;
      mirror it here. — **features-service@ba5143fd**. `routing_key="global"` confirmed via 3 independent sources (the
      repro's own env vars, SKILL.md's "calendar collapses to a single GLOBAL cell", and `launch-features-vm.sh`'s own
      comment "`get_data_sink(routing_key=ag.lower())` ... AG-keyed + base fallback both set (calendar=GLOBAL)").
      `get_source_bucket()` now calls `get_data_sink(routing_key="global")` first, falls back to
      `resolve_bucket(kind="features-calendar")`; 2 regression tests added in `tests/unit/test_config.py`
      (override-honoured + SSOT-fallback), mirroring
      `test_get_output_bucket_honours_data_sink_override`/`_falls_back_to_ssot`. Full `quality-gates.sh` green
      (sentinel-verified by quickmerge --agent); shipped via quickmerge, landed on `live-defi-rollout`.
- [ ] [DATA] P1. **features-service / operator** — audit
      `gs://features-calendar-prd-central-element-323112/     calendar/{time_features,economic_events}/` for objects
      written by prior test/smoke-check invocations (anomalous zero-row parquets, or objects whose `written_at`/manifest
      provenance correlates with a known test-harness run rather than the real scheduled batch job) — determine whether
      any cleanup is needed. Scope this as its own audit; do not block the config fix above on it.
- [ ] [SCRIPT] P2. **features-service** — audit every OTHER feature family's config for the same declared-but-unconsumed
      `is_test_run` pattern (this bug's root cause — a field that LOOKS like it's wired up because it's declared with
      the right description, but isn't consulted anywhere) — `volatility`, `onchain`, `sports`, `cross_instrument`,
      `multi_timeframe`, `commodity` all declare their own `is_test_run` field per the grep pattern seen in `delta_one`;
      verify each one's `get_output_bucket`-equivalent actually branches on it (or routes through `get_data_sink`)
      rather than assuming delta_one's correctness generalizes.
