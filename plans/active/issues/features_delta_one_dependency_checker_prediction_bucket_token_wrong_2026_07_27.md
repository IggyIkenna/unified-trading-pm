---
doc_type: issue
title:
  features-service delta_one's dependency checker resolves the WRONG market-data-tick bucket name for PREDICTION
  ("prediction" instead of "pred") — every PREDICTION:delta_one run fails its MDPS dependency check regardless of real
  data availability
summary: >-
  Running `/data-pipeline-check-features`'s benchmark leg for `PREDICTION:delta_one` (day=2026-07-19, 7-day window), the
  run failed its upstream dependency check with "The specified bucket does not exist" for
  `market-data-tick-prediction-central-element-323112`. The REAL bucket (confirmed via `gcloud storage buckets list`) is
  `market-data-tick-pred-prd-central-element-323112` — PREDICTION is the one asset_group whose bucket-name token is
  abbreviated to `pred`, not spelled out. `features_service/delta_one/app/core/dependency_checker.py`'s
  `_format_template_vars` does a naive `asset_group.lower()` with no abbreviation mapping, so every PREDICTION
  dependency check is checking a bucket that has never existed — this fails BEFORE the real data-availability question
  is ever asked, for every day, regardless of whether MDPS candles actually exist.
status: open
nature: issue
asset_group: [prediction]
stage: [data]
repos: [features-service]
scope: [engineer, admin]
tags: [features-service, delta-one, dependency-checker, bucket-naming, prediction, config-bug]
related:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /codex/02-data/per-asset-group-bucket-layouts.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-07-27
priority: P2
parent_epic: infrastructure_master
source: "slot-3, infra, todo 10 benchmark work (data_pipeline_check_mdps_features_2026_07_20.md), 2026-07-27"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by:
locked_by:
locked_since:
---

# delta_one dependency checker resolves the wrong PREDICTION bucket name

## What I found

Running the `/data-pipeline-check-features` benchmark leg for `PREDICTION:delta_one` (day=2026-07-19, 7-day window
2026-07-12..2026-07-19), the VM (`features-e2e-prediction-20260727-184853-0f2a85`) failed its dependency check
immediately:

```
ERROR Missing: market-data-processing-service
ERROR   Path: gs://market-data-tick-prediction-central-element-323112/processed_candles/by_date/day=2026-07-12/
ERROR   Reason: 404 ... The specified bucket does not exist.
```

**Confirmed via `gcloud storage buckets list --filter="name~'market-data-tick'"`** — the real bucket is
`market-data-tick-pred-prd-central-element-323112` (and its `-test-` sibling `market-data-tick-pred-test-...`). Every
other asset_group uses its full name as the bucket token (`cefi`, `defi`, `tradfi`, `sports`) — **PREDICTION is the one
outlier abbreviated to `pred`**, and the checker's bucket name is missing BOTH the abbreviation AND the `-prd-` env-tier
segment entirely.

**Root cause (direct code read)**: `features_service/delta_one/app/core/dependency_checker.py`:

```python
UPSTREAM_DEPS: ClassVar[dict[str, dict[str, object]]] = {
    "market-data-processing-service": {
        "bucket_template": "market-data-tick-{asset_group_lower}-{project_id}",
        ...
```

and `_format_template_vars` (same file):

```python
def _format_template_vars(self, date: str, asset_group: str) -> dict[str, str]:
    return {..., "asset_group_lower": asset_group.lower(), ...}
```

`asset_group.lower()` on the CLI-passed `"PREDICTION"` produces `"prediction"` — there is no abbreviation-mapping step
anywhere in this file translating it to `"pred"`. This is EXACTLY the same class of bug this file's own comment (lines
~108-114) documents as already found and fixed on the OUTPUT-bucket side: a now-deleted `OUTPUT_BUCKETS` map named
`features-delta-one-prediction-{pid}` when the real bucket was `features-delta-one-pred-*` — fixed by routing output
resolution through `features_service.delta_one.config.get_output_bucket()`, which correctly resolves via the canonical
`cloud-providers.yaml`. **The upstream/input side (this dependency checker's `market-data-tick` bucket resolution) never
got the same fix** — it still hand-rolls the bucket name from a raw template string instead of going through a canonical
resolver that knows about the `pred` abbreviation.

**Not fully resolved this session**: the `UPSTREAM_DEPS` (non-test) `bucket_template` string
(`"market-data-tick-{asset_group_lower}-{project_id}"`) is ALSO missing the `-prd-` env-tier segment that every real
prod bucket has (confirmed: `market-data-tick-tradfi-prd-...`, `market-data-tick-cefi-prd-...`, etc. all have `-prd-`).
Yet a same-session `TRADFI:delta_one` dependency-check failure correctly showed the FULL, correct path
(`market-data-tick-tradfi-prd-central-element-323112/...`) — meaning either this exact `UPSTREAM_DEPS` template isn't
actually the one hit at runtime for non-PREDICTION asset_groups (a different resolution path may be in play that I
didn't fully trace), or `test_mode` behaves differently than assumed. Flagging as unresolved rather than guessing — the
PREDICTION-specific "prediction" vs "pred" token bug is independently confirmed and actionable regardless of this open
question.

## Why it matters

- **Every PREDICTION:delta_one run fails before the real data-availability question is ever asked** — the dependency
  check can never succeed for PREDICTION regardless of whether MDPS candles genuinely exist for the requested date,
  because it's checking a bucket that has never existed. This masks the REAL, separately-confirmed finding (PREDICTION
  MDPS candle production has a ~6-month gap, 2026-01-14 through ~2026-07-24, only just resuming) behind a config/naming
  bug that would ALSO block a request for a day that DOES have real data (e.g. 2026-07-25/26, confirmed to exist in the
  real bucket).
- Blocks `todo 10`'s benchmark measurement for `PREDICTION:delta_one` entirely — no throughput number can be measured
  until this is fixed (or `--skip-dependency-check` is used, not recommended per the checker's own guidance).
- The exact same bug class already bit the OUTPUT side and was fixed — this is the input-side twin, previously missed.

## Recommended fix path

- [ ] [SCRIPT] P2. Route `features_service/delta_one/app/core/dependency_checker.py`'s `market-data-tick` bucket
      resolution through a canonical resolver (mirroring the already-shipped output-side fix via
      `get_output_bucket()`/`cloud-providers.yaml`) instead of the raw `bucket_template.format(asset_group_lower=...)`
      approach — so the `pred` abbreviation (and any other asset_group-specific bucket-token exceptions) resolve
      correctly without a hand-maintained per-family template string. Add a regression test asserting
      `asset_group="PREDICTION"` resolves to a bucket containing `pred` (not `prediction`), mirroring whatever test
      already exists for the output-side fix.
- [ ] [SCRIPT] P3. Investigate and resolve the `UPSTREAM_DEPS` (non-test) `bucket_template`'s apparent missing `-prd-`
      segment (`"market-data-tick-{asset_group_lower}-{project_id}"`) against the observed-correct TRADFI path
      (`market-data-tick-tradfi-prd-...`) — determine whether this exact template/class is actually invoked for
      non-test-mode delta_one runs, or a different resolution path is in play; fix whichever is found to be wrong.
- [ ] [DATA] P3. Once the bucket-naming bug is fixed, re-run
      `/data-pipeline-check-features --family delta_one     --asset-group PREDICTION` for a day within the now-resumed
      candle-production window (≥2026-07-25) to get a genuine benchmark measurement — day=2026-07-19 (used this session)
      falls inside the confirmed ~6-month production gap and would still fail on data-availability even with the naming
      bug fixed.
