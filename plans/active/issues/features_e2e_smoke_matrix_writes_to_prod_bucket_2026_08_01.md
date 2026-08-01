---
doc_type: issue
title:
  ALL 8 `e2e-testing/scripts/<family>/smoke_matrix.py` harnesses write/read against PROD buckets, not the `-test-`
  buckets they claim — `IS_TEST_RUN=true` alone is insufficient, `PROTOCOL_DATA_SINK_BUCKET*` is required and never set
summary: >-
  Live-verified while executing `cross_cutting_satellite_ao_dispatch_batch2-002` (features-service catalogue
  completeness + smoke-check masking test): every `e2e-testing/scripts/<family>/smoke_matrix.py`'s `_invoke_cli()`
  subprocess env sets ONLY `IS_TEST_RUN=true`, never
  `PROTOCOL_DATA_SINK_BUCKET`/`PROTOCOL_DATA_SINK_BUCKET_{AG|GLOBAL}`. Each family's own
  `get_output_bucket()`/`get_source_bucket()` (the CORRECT, already-fixed pattern per
  `features_calendar_is_test_run_ignored_writes_prod_2026_07_27.md`) resolves the test bucket ONLY via
  `get_data_sink(routing_key=...)` picking up that override env var — `IS_TEST_RUN` itself is NOT consulted by that
  resolution path at all. Verified live for 3 families (commodity, calendar, delta_one — all 3 resolved to their PROD
  bucket name under bare `IS_TEST_RUN=true`); the remaining 5 (cross_instrument, multi_timeframe, onchain, sports,
  volatility) share the identical `_invoke_cli()` code shape (byte-identical `env["IS_TEST_RUN"] = "true"` line, no
  `PROTOCOL_DATA_SINK_BUCKET*` anywhere in any of the 8 files) so the same failure is near-certain there too, though not
  individually live-verified this session. This means the "institutional smoke matrix" design's own stated contract —
  every file's docstring says "verify GCS parquet under -test- bucket" / "TEST manifest row" — has been FALSE for every
  family, for an unknown period, every time these harnesses actually ran a non-dry-run leg.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [e2e-testing, features-service]
scope: [engineer, admin]
tags:
  [
    data-pipeline,
    data-correctness,
    features,
    e2e-testing,
    smoke-matrix,
    test-bucket-isolation,
    prod-pollution-risk,
    big-finding,
  ]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/issues/features_calendar_is_test_run_ignored_writes_prod_2026_07_27.md,
    /plans/archive/issues/features_sports_is_test_run_ignored_writes_real_data_to_prod_2026_07_27.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    /codex/05-infrastructure/gcs-object-operations.md,
  ]
created: "2026-08-01"
last_updated: "2026-08-01"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.65
assigned_role: data_engineering
drift_direction: advance-code
source:
  "slot-13, data_engineering, discovered while executing cross_cutting_satellite_ao_dispatch_batch2-002 (features
  catalogue completeness + smoke-check masking empirical test), 2026-08-01 — BIG FINDING, operator attention requested"
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# `smoke_matrix.py` harnesses silently target PROD buckets — `IS_TEST_RUN=true` alone does not route to `-test-`

## What I found

Running `e2e-testing/scripts/commodity/smoke_matrix.py` and `e2e-testing/scripts/calendar/smoke_matrix.py` for real (not
`--dry-run`) as part of the empirical smoke-check-masking test required by
`cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md`'s catalogue-completeness todo, both cells resolved to a
**PROD** bucket, not a `-test-` bucket, despite each subprocess invocation carrying `IS_TEST_RUN=true` (the ONLY env var
`_invoke_cli()` sets, in every one of the 8 `smoke_matrix.py` copies):

```
$ IS_TEST_RUN=true GCP_PROJECT_ID=central-element-323112 python -c \
    "from features_service.calendar.config import get_config; print(get_config().get_source_bucket())"
features-calendar-prd-central-element-323112          # <- PROD, should be -test-

$ IS_TEST_RUN=true GCP_PROJECT_ID=central-element-323112 python -c \
    "from features_service.commodity.config import get_settings; print(get_settings().get_output_bucket())"
commodity-signals-batch-central-element-323112         # <- prod-named (commodity has no -test- variant reachable this way)

$ IS_TEST_RUN=true GCP_PROJECT_ID=central-element-323112 python -c \
    "from features_service.delta_one.config import get_settings; print(get_settings().get_output_bucket('TRADFI'))"
features-tradfi-prd-central-element-323112             # <- PROD, even for delta_one, the "already-fixed" reference family
```

Setting the override env var explicitly makes calendar correctly route to `-test-`:

```
$ IS_TEST_RUN=true PROTOCOL_DATA_SINK_BUCKET_GLOBAL=features-calendar-test-central-element-323112 \
  PROTOCOL_DATA_SINK_BUCKET=features-calendar-test-central-element-323112 GCP_PROJECT_ID=central-element-323112 \
  python -m features_service.calendar --operation compute --mode batch --start-date 2026-08-01 --end-date 2026-08-01
...
INFO [1/1] 2026-08-01 [economic_events]: 0 rows written to gs://features-calendar-test-central-element-323112/...
```

**Root cause**: the per-family config classes (`CalendarFeaturesConfig.get_source_bucket()`,
`CommodityFeaturesConfig.get_output_bucket()`, `FeaturesDeltaOneConfig.get_output_bucket()`) resolve their bucket via
`get_data_sink(routing_key=...)` picking up `PROTOCOL_DATA_SINK_BUCKET`/`PROTOCOL_DATA_SINK_BUCKET_{AG|GLOBAL}` env vars
FIRST, falling back to the prod-named SSOT resolution when unset. This is the exact, already-shipped, correct fix from
`features_calendar_is_test_run_ignored_writes_prod_2026_07_27.md` (`features-service@ba5143fd`) — that fix is real and
working. But **`IS_TEST_RUN` itself is never consulted by that resolution path** — it's a separate, cosmetic config
field (`is_test_run: bool`) that nothing downstream reads for bucket routing. The bug is entirely on the **caller
side**: `e2e-testing/scripts/<family>/smoke_matrix.py`'s `_invoke_cli()` sets `env["IS_TEST_RUN"] = "true"` and stops
there — it never derives/sets the matching `PROTOCOL_DATA_SINK_BUCKET*` var, so the subprocess it launches falls
straight through every family's fallback branch to the PROD bucket name. Confirmed byte-identical across all 8 files:

```
$ grep -n 'env\[' e2e-testing/scripts/*/smoke_matrix.py
scripts/calendar/smoke_matrix.py:171:          env["IS_TEST_RUN"] = "true"
scripts/commodity/smoke_matrix.py:163:         env["IS_TEST_RUN"] = "true"
scripts/cross_instrument/smoke_matrix.py:162:  env["IS_TEST_RUN"] = "true"
scripts/delta_one/smoke_matrix.py:171:         env["IS_TEST_RUN"] = "true"
scripts/multi_timeframe/smoke_matrix.py:161:   env["IS_TEST_RUN"] = "true"
scripts/onchain/smoke_matrix.py:201:           env["IS_TEST_RUN"] = "true"
scripts/sports/smoke_matrix.py:305:            env["IS_TEST_RUN"] = "true"
scripts/volatility/smoke_matrix.py:163:        env["IS_TEST_RUN"] = "true"
```

Live-verified the prod-fallthrough for 3 of the 8 families (commodity, calendar, delta_one); the other 5 share the
identical `_invoke_cli()` shape so are near-certain but not individually re-verified this session (scoping this todo's
"done when" to cover them explicitly rather than assuming).

## Why it matters

- **Every real (non-`--dry-run`) `smoke_matrix.py` invocation across every family has been polluting/reading PROD data
  since the batch1b relocation to `e2e-testing/scripts/<family>/`** (and quite possibly before, if the pre-relocation
  `features-service/scripts/<family>/smoke_matrix.py` copies had the same gap — not checked, out of this todo's scope).
  This is the SAME failure class already fixed once for calendar's _config_ layer
  (`features_calendar_is_test_run_ignored_writes_prod_2026_07_27.md`) and once for sports's config layer
  (`features_sports_is_test_run_ignored_writes_real_data_to_prod_2026_07_27.md`) — but those fixes only closed the
  config-side half of the contract. The CALLER side (this harness) was never updated to actually set the env vars the
  fixed config now depends on, so the fix is invisible to every automated smoke run.
- Directly undermines the credibility of `cross_cutting_satellite_ao_dispatch_batch2-002`'s own empirical
  smoke-check-masking test (see companion doc
  `features_service_catalogue_completeness_smoke_masking_findings_2026_08_01.md`) — a "PASS" from `smoke_matrix.py` was
  never proof the FAMILY's test-tier pipeline works; it may only prove the PROD-tier pipeline works (or doesn't).
- Every `/data-pipeline-check-features`-class audit that trusts `smoke_matrix.py`'s "writes are test-bucket-only" claim
  (per each file's own docstring) has been trusting a false premise.

## Recommended decision

- [x] ✅ [SCRIPT] P0. **e2e-testing** — for each of the 8 `scripts/<family>/smoke_matrix.py` files, extend
      `_invoke_cli()` to derive and set the correct `PROTOCOL_DATA_SINK_BUCKET*` override alongside `IS_TEST_RUN=true`,
      matching that family's own `routing_key` convention (`"global"` for calendar per the archived fix; `"commodity"`
      for commodity; `asset_group.lower()` for delta_one/cross_instrument/multi_timeframe/onchain/volatility; whatever
      sports's config actually reads — verify per-family, do not assume one shape fits all). Test-bucket NAME should
      derive from each family's existing `_test_bucket()` helper (already computes the correct `-test-` bucket name per
      family) — set the env var to that SAME value so the subprocess and the verifier agree on which bucket to check. —
      **e2e-testing@04d261d**. Per-family routing_key verified against each config's actual
      `get_data_sink(routing_key=...)` call (code read, not assumed): `"global"` calendar, `"commodity"` commodity,
      `"defi"` onchain (matches `_ONCHAIN_ASSET_GROUP`), `"sports"` sports, `asset_group.lower()`
      delta_one/cross_instrument/multi_timeframe/volatility. **Also fixed**: 5 families'
      `_test_bucket()`/`TEST_BUCKET_TEMPLATE` were stale, referencing PRE-Fold-A per-kind bucket names
      (`features-delta-one-*` etc.) that Fold A (2026-07-18/19) retired — `resolve_bucket()` now RAISES
      `BucketNamingError` on those kinds. Corrected to the folded `features-{ag}-test-{pid}` shape (already-provisioned,
      confirmed via `client.bucket(...).exists()` against live GCS — `gsutil` itself had expired/invalid creds and
      falsely reported all as missing, a red herring caught and worked around). **Done-when evidence** (real,
      non-dry-run runs against live GCS, `central-element-323112`): calendar — FULL E2E:
      `0 rows written to gs://features-calendar-test-central-element-323112/calendar/{time_features,economic_events,yield_curve,economic_results}/by_date/day=2026-08-01/features.parquet`,
      exit 0. onchain — FULL E2E:
      `ManifestWriter: updated availability index (1 total entries, 1 new) in features-defi-test-central-element-323112`,
      "Processing completed successfully", exit 0. delta_one (CEFI) — real manifest write confirmed landing at
      `gs://features-cefi-test-central-element-323112` (feature compute itself hit an unrelated pre-existing
      universe-filter issue, tracked below). commodity, cross_instrument, multi_timeframe, sports, volatility — full
      end-to-end runs blocked by separate pre-existing issues (Baker Hughes adapter regression already tracked;
      multi_timeframe CLI fully broken; stale manifest consolidators; missing upstream options/futures data) — bucket
      **resolution** independently confirmed correct for all 5 via direct `get_output_bucket()`/equivalent calls using
      the exact env vars this fix sets (each resolved to its `-test-` bucket, not PROD). Full `quality-gates.sh` green
      (108s, sentinel-verified); shipped via quickmerge, landed + verified on `live-defi-rollout`. **New findings from
      this verification exercise** (multi_timeframe CLI entirely broken; calendar/delta_one smoke-harness verifier
      prefix mismatches; 2 stale manifest consolidators) filed as
      `/plans/active/issues/features_smoke_matrix_verification_findings_2026_08_01.md` per the FINDINGS CLOSURE rule —
      none block this todo's own P0 scope, which is proven correct independent of them.
- [ ] [DATA] P1. **features-service / operator** — once (P0 above) lands, audit each family's PROD features bucket for
      any historical test-shaped pollution left over from the pre-fix era (mirroring the audit already done for calendar
      in `features_calendar_is_test_run_ignored_writes_prod_2026_07_27.md`'s P1 todo) — scope to objects/rows whose
      `day=`/date matches a known smoke-test invocation window, not a blind full-bucket sweep. Follow the
      reversibility-qualified delete protocol (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a) for any
      confirmed test-artifact deletion.
- [ ] [DATA] P2. Once P0 lands, re-run every family's `smoke_matrix.py` for real and confirm PASS against the
      GENUINELY-test-isolated bucket (not the accidental prod success some cells currently show) — this is the actual
      proof the "institutional smoke matrix" contract now holds. **⚠️ BLOCKED — do NOT run this cold.** Re-running
      `smoke_matrix.py` (the cross_instrument family especially) re-triggers the unbounded-memory runaway that caused
      the 2026-08-01 **second AO outage** (38.8GB RSS over 4.5h; its `timeout 150` wrapper AND a direct SIGTERM both
      ignored; SIGKILL required) — see
      `/plans/active/issues/features_cross_instrument_smoke_verify_unbounded_memory_second_ao_outage_2026_08_01.md`.
      This todo's backlog task (`features_e2e_smoke_matrix_writes_to_prod_bucket-003`) is PARKED behind prereq
      `features_smoke_verify_timeout_hardening_landed` (set by main-orchestrator 2026-08-01) and will not dispatch until
      that incident doc's `[INFRA]` timeout/memory-bounding fix lands. Do NOT flip this checkbox or unpark before then.

## Progress Log

- 2026-08-01 (slot-13, data_engineering): Discovered while executing `cross_cutting_satellite_ao_dispatch_batch2-002`'s
  empirical smoke-check-masking test (task scope: catalogue completeness + masking, NOT this bug) — filed immediately
  per the "big finding" / data-pipeline-correctness escalation rule rather than absorbing the multi-file cross-family
  fix into that task's scope. NOT fixed this session.
- 2026-08-01 (slot-12, data_engineering): P0 DONE — `e2e-testing@04d261d`. See the checkbox above for full evidence.
  Verifying the fix live surfaced a stale-bucket-naming gap (5 families' `_test_bucket()` used bucket names Fold A
  retired) that was fixed inline (same file, blocking), plus 4 unrelated pre-existing bugs filed separately as
  `/plans/active/issues/features_smoke_matrix_verification_findings_2026_08_01.md`. A separate incident
  (`features_service.cross_instrument`'s real compute run growing to ~38.8GB RSS over hours, ignoring its `timeout`
  wrapper, causing a second same-day AO outage) happened mid-verification — the runaway PID was killed immediately on
  the operator's notification; that incident is tracked in its own doc by the agent who filed it, not duplicated here.
  P1/P2 todos below are unstarted.
