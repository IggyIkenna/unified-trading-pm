---
doc_type: issue
title: >-
  data-pipeline-check-features's --env staging fix (for the IAM issue) makes SPORTS reference-data reads target the
  empty staging tier instead of real prod data — no source-bucket override exists for sports, unlike delta_one
summary: >-
  Fixing `pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md` (features-service@524b71ef, `--env staging`
  so the VM runs as `uts-test-sa` instead of `uts-prd-sa`) correctly unblocked the IAM/write-path problem, but exposed a
  SECOND, independent gap for the `sports` feature family specifically:
  `features_service/sports/data/gcs_paths.py::resolve_instruments_bucket()` / `resolve_tick_data_bucket()` route
  reference-data READS through the yaml-SSOT `resolve_bucket()` helper, which is env-tiered by design
  (`instruments-store-sports-{env}-{pid}`) — with NO source-bucket-style override to decouple reads from the VM's own
  `DEPLOYMENT_ENV`. Every reference entity (fixtures, standings, odds, etc.) legitimately reads from
  `instruments-store-sports-stg-...` under `--env staging`, and that tier has never been seeded with real sports
  reference data — so the compute always finds "17/17 entities missing" and correctly (per the honest-absence model)
  records `empty_confirmed`, even for `SPORTS_SMOKE_DATES`' explicitly-"busy" days that have real fixtures in the
  `-prd-` tier.
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [features-service]
scope: [engineer]
tags: [pipeline-e2e-check, sports, honest-absence, bucket-routing, iam]
related:
  [
    plans/active/issues/pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
created: "2026-08-01"
parent_epic: infrastructure_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [sports_consolidated_native_ao_extract-032]
resolved_by:
  plan_reconciler 2026-08-02 -- all todos verified [x] with HARD evidence (sha/artifact), no un-migrated deferred work
  found. See /plans/active/issues/plan_reconciler_findings_undefined.md.
locked_by:
context_scope: [/codex/02-data/honest-absence-downstream-handling.md]
depends_on: []
---

# sports feature e2e-check reads empty staging-tier reference data, not real prod data

## What I found

After shipping the `--env staging` fix (`features-service@524b71ef`) and a supporting IAM grant (see
`pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md`), re-ran the Track K (features) baseline checkpoint
for `SPORTS:sports` day `2025-12-20` (a `SPORTS_SMOKE_DATES` "busy" day, chosen specifically because it has known real
fixtures). The force leg completed cleanly (`exit_status=0`, `run.log` fully populated — both prior blockers genuinely
fixed) but reported:

```
WARNING Reference data for 2025-12-19: 17/17 entities missing — ['leagues', 'teams', 'standings', ...]
WARNING No GCS reference data found for 2025-12-19
INFO sports batch startup gate: instruments-store consolidator healthy for sports
     (bucket=instruments-store-sports-stg-central-element-323112)
```

Compare to the SAME day's read under the pre-fix (`uts-prd-sa`, implicit `DEPLOYMENT_ENV=prod`) run, which read real
data fine before crashing on the WRITE side:
`GCS read standings: 574 rows from gs://instruments-store-sports-prd-central-element-323112/...`,
`GCS read fixtures: 324 rows`, etc.

**Root cause**: `features_service/sports/data/gcs_paths.py::resolve_instruments_bucket()` (used by
`gcs_reader.py::read_reference_entity`, the actual reference-data fetch) and the parallel `resolve_tick_data_bucket()`
both route through `features_service.common.resolve_bucket(kind=..., asset_group="sports")` — explicitly documented as
always returning the **env-tiered** form (`instruments-store-sports-{env}-{pid}` /
`market-data-tick-sports-{env}-{pid}`), by design, "never the legacy no-env form." There is no
`--source-bucket`-equivalent override for sports the way `pipeline_e2e_check.py`'s `_build_launch_argv` provides for
`delta_one`'s downstream families (`multi_timeframe`/`cross_instrument` read delta_one's freshly-written `-test-` output
via an explicit `source_bucket` param) — `source_bucket` is ONLY ever populated from `FeatureFamily.DELTA_ONE`'s own
test sink (`pipeline_e2e_check.py:1977`), never wired to sports at all. So under `--env staging`, sports reference reads
have no way to target `-prd-` while writing to `-test-` — the two are coupled via one env-derived bucket name.

**`instruments-store-sports-stg-central-element-323112` has never been seeded** with real reference data (it's a
genuinely empty tier, not a stale/lagging one) — confirmed by "17/17 entities missing" across every entity type, not a
partial gap.

This is NOT a bug in the honest-absence machinery itself — `empty_confirmed` IS the correct, honest verdict for what the
compute actually saw (a genuinely empty staging bucket). The problem is one layer up: the e2e-check's own premise
("prove the compute pipeline works against real data") is silently defeated for sports specifically, because the input
it reads isn't real data at all.

## Why it matters

- **Every sports feature e2e-check checkpoint (past and future, until this is fixed) will report `empty_confirmed`
  regardless of which day is targeted** — including deliberately-chosen "busy" SPORTS_SMOKE_DATES days with abundant
  real fixtures. The checkpoint mechanically PASSES (force leg exits 0, writes an honest `empty_confirmed` manifest row)
  but does NOT prove the sports feature-computation LOGIC actually works against real inputs — only that the VM boots,
  has the right IAM, and the honest-absence path itself functions correctly.
- **This is a real correctness gap someone could easily miss**: a report reading "PASSED, empty_confirmed: source
  legitimately had no data for this window" reads as a clean, complete proof unless you cross-check against the actual
  `run.log` and notice the bucket resolved is `-stg-`, not `-prd-`. Future users of the `data-pipeline-check-features`
  skill for `sports` should NOT treat a clean `empty_confirmed` result as proof the compute logic works — only that the
  plumbing/IAM does.
- **Does not affect other families/asset_groups** the same way — `delta_one`'s own read-source override mechanism
  already exists (and is exercised); this is sports-specific because its reference-data reader has no equivalent.

## Recommended decision (not unilaterally fixed here — real design work)

1. **Add a source-bucket-style override** to `resolve_instruments_bucket()`/`resolve_tick_data_bucket()` (e.g. an
   optional explicit-env param, or a `PROTOCOL_DATA_SOURCE_BUCKET_SPORTS`-style env var mirroring the existing
   `PROTOCOL_DATA_SINK_BUCKET_SPORTS` sink override), threaded from `pipeline_e2e_check.py`'s sports shard build so
   e2e-checks can read real `-prd-` reference data while still writing to `-test-` output — matching the architecture
   principle every other family already follows ("input stays the PROD source bucket").
2. **Alternative**: seed real reference data into the `-stg-` tier for sports (a one-time backfill/ copy job) — simpler
   but duplicates real data into a tier meant to stay isolated/ephemeral, and would need re-seeding as new dates are
   added; probably the WORSE option long-term.
3. This needs an operator/main call on which approach — not a unilateral pick, since it touches the sports
   bucket-routing SSOT (`gcs_paths.py`'s own docstring explicitly protects the env-tiered behavior as intentional).

## Todos

- [x] ✅ [CODE] P1. Design + implement a source-bucket override for sports reference-data reads
      (`features_service/sports/data/gcs_paths.py`), threaded through `pipeline_e2e_check.py`'s sports shard build, so a
      `-test-`-sink e2e-check run can read real `-prd-` reference data. Verify with a fresh force leg against a
      `SPORTS_SMOKE_DATES` busy day and confirm it reports a REAL (non-empty) write, not `empty_confirmed`. (repo:
      features-service) — features-service@72393fbf. **Real-VM verification caught a bug in the first implementation
      (247ecdaa)**: `get_data_source()`'s provider silently defaulted to "local" (no launcher sets
      `PROTOCOL_DATA_SOURCE_BACKEND` for sports), so the override no-opped and reads still hit the never-seeded `-stg-`
      tier despite a unit test that hand-set the backend var passing. Fixed by switching
      `resolve_instruments_bucket()`/`resolve_tick_data_bucket()` to the same direct pydantic-field pattern
      `FeaturesCrossInstrumentConfig.get_input_bucket()` already uses successfully (features-service@8ea48a33, test-data
      fixup @72393fbf). Final force-leg (day=2025-12-20, VM `features-e2e-sports-20260801-124529-281e78`) confirms REAL
      reads — `GCS read leagues: 1228 rows`/`standings: 574 rows`/etc. from `instruments-store-sports-prd-...` — and the
      checkpoint report shows `parquet=6, manifest=captured` (not `empty_confirmed`).
- [x] ✅ [DOC] P2. Noted this limitation in the `data-pipeline-check-features` skill doc
      (`cursor-configs/skills/data-pipeline-check-features/SKILL.md`), as a ⚠️ callout right after the existing
      "Required INPUT per family" table's Reality-check callout (same pattern/style) — so a future run doesn't mistake a
      clean `empty_confirmed` sports result for genuine proof the compute logic works. (repo: unified-trading-pm, same
      commit as this checkbox flip)

## Codex SSOTs

`/codex/02-data/honest-absence-downstream-handling.md`.
