---
doc_type: issue
title: First-ever complete CF-manifest-audit rollup (2026-07-26) — a false-positive checker bug (fixed) plus genuine cross-AG CF-8/Era-B/CF-3/CF-4 reds needing data-team triage
summary: >-
  The scheduled `uts-prod-cf-manifest-audit` Cloud Run Job had never completed a full run since
  it was created (14+ consecutive daily OOM failures, root-caused + fixed in
  `cf_manifest_audit_scheduled_job_daily_failure_2026_07_13.md`). The first-ever complete
  10-bucket rollup (2026-07-26, `gs://cf-manifest-audit-central-element-323112/cf_audit/2026-07-26.json`)
  surfaced two classes of finding: (1) a checker bug — CF-2-paths/CF-3-partition read RED on
  10/10 buckets because `_probe_paths()`'s shallow descent always picked an irrelevant
  `_`-prefixed metadata/backup dir over real data (fixed same-session,
  `unified-trading-library@21069582`); (2) genuine, previously-invisible reds — CF-8
  (`available_at`) is RED on 5 of 10 buckets across 4 different asset_groups, and Era-B /
  CF-3 / CF-4 are RED on buckets a prior doc's Adjudication had marked "already-confirmed"
  GREEN. This doc tracks class (2) for data-team triage; class (1) is closed, cited for the
  record only.
status: open
resolved_by:
nature: notes
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-library, market-tick-data-service]
scope: [engineer, admin]
tags: [cf-manifest-audit, data-correctness, cross-cutting, cf-8, era-b, cefi, tradfi, sports, prediction]
related:
  [
    /plans/active/issues/cf_manifest_audit_scheduled_job_daily_failure_2026_07_13.md,
    /plans/active/issues/cross_cutting_manifest_canonicalisation_findings_2026_07_11.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
  ]
created: 2026-07-26
parent_epic: infrastructure_master
priority: P2
source:
  [
    "gs://cf-manifest-audit-central-element-323112/cf_audit/2026-07-26.json (execution uts-prod-cf-manifest-audit-qsp6r)",
    "Cloud Logging for uts-prod-cf-manifest-audit, 2026-07-26T21:14-21:18Z",
  ]
assigned_vm: NA
locked_by:
execution_scope: local-only
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
---

# First complete CF-audit rollup — a fixed checker bug + genuine cross-AG data-quality reds

## Context

`uts-prod-cf-manifest-audit` never wrote a single successful daily output in its entire
existence — every run from at least 2026-06-27 through 2026-07-26 (30 checked days) failed,
first on a silent exec bug then on an OOM (see
`cf_manifest_audit_scheduled_job_daily_failure_2026_07_13.md`). Fixing the OOM
(`unified-trading-library@6ce1ddb6` + a Cloud Run memory bump to 32Gi/8vCPU) let the job
complete for the first time ever, 2026-07-26 21:14-21:18 UTC (execution
`uts-prod-cf-manifest-audit-qsp6r`), writing
`gs://cf-manifest-audit-central-element-323112/cf_audit/2026-07-26.json`.

## Finding 1 — CF-2-paths/CF-3-partition false RED on 10/10 buckets (FIXED, cited for the record)

Every single sample path `_probe_paths()` returned was from an irrelevant top-level
metadata/scratch dir (`_migration_backup`, `_catalogue`, `_manifests`, `_cache`,
`_legacy_migrated_processed`, `_audits`, `_backups`) — never real `category=`/`asset_group=`
hive-partitioned data. GCS `ls` returns lexicographic order and `_` sorts before lowercase
`a-z`, so `data_kids[0]` always preferred one of these over real data; the old exclusion
enumerated only 4 specific names (`_index`/`_vm_staging`/`backfill-logs`/`snapshots`), missing
every other underscore-prefixed dir. **Fixed same-session**: `unified-trading-library@21069582`
generalizes the exclusion to "any top-level dir whose basename starts with `_`" (this
workspace's own metadata-dir naming convention), with 5 new regression tests reproducing the
exact live pattern. Not yet visible in a live re-run — the fix ships in a UTL release; the MTDS
image (which bundles UTL) needs to pick up the new pin before the NEXT scheduled 06:00 UTC run
reflects it. **Action**: re-check tomorrow's run; if CF-2-paths/CF-3-partition are still RED
after the image picks up the new UTL pin, that's a genuine regression, not this bug recurring.

## Finding 2 — genuine reds needing data-team triage (NOT fixed here — out of this task's scope)

Full per-bucket rollup (excluding the Finding-1 false positives above):

| bucket | genuine reds |
| --- | --- |
| `market-data-tick-cefi-prd` | CF-1, CF-3, CF-4, CF-8, Era-B |
| `instruments-store-cefi-prd` | (clean) |
| `market-data-tick-defi-prd` | (clean) |
| `instruments-store-defi-prd` | (clean) |
| `market-data-tick-tradfi-prd` | CF-8, Era-B |
| `instruments-store-tradfi-prd` | (clean) |
| `market-data-tick-sports-prd` | CF-8 |
| `instruments-store-sports-prd` | CF-3, CF-4, CF-8 |
| `market-data-tick-pred-prd` | CF-8 |
| `instruments-store-pred-prd` | (clean) |

Two things stand out:

1. **cefi's CF-1/CF-4/CF-5/Era-B red is ALREADY a tracked todo** — see
   `plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` todo "Bring cefi's
   raw_tick_data manifest to CF-1/CF-4/CF-5/Era-B GREEN" (source:
   `cross_cutting_manifest_canonicalisation_findings_2026_07_11.md`). This live rollup is fresh
   confirming evidence for that todo — no new todo needed for cefi. (Note: this live run also
   shows cefi CF-3 RED, which that todo's scope list does not mention — worth folding in when
   that todo is worked.)
2. **CF-8 (`available_at`) RED on 4 of 5 asset_groups (cefi/tradfi/sports/prediction, 5 of 10
   buckets) is NEW** — this column check has never run to completion before, so this is the
   first real evidence of it. It is NOT mentioned in the cefi todo's scope, and the source doc's
   language ("prediction/sports/tradfi/defi's already-confirmed state") reads as GREEN for
   tradfi/sports/prediction, which this live run contradicts for CF-8 (and Era-B on tradfi, and
   CF-3/CF-4 on sports/instruments-store). Only defi reads fully clean.

## Recommended decision

Data-team triage each genuine red above; cefi's already has a home (todo cited). The rest need
new todos:

- [ ] [DATA] P2. Diagnose + fix CF-8 (`available_at` non-null coverage) RED on
      `market-data-tick-tradfi-prd`, `market-data-tick-sports-prd`,
      `instruments-store-sports-prd`, `market-data-tick-pred-prd` (cefi's CF-8 folds into the
      existing cefi todo above). Re-run `cf_manifest_audit.py` per-bucket after each fix to
      confirm GREEN. Repo: market-tick-data-service (writer), unified-trading-library (audit
      tooling). Source: this doc, `gs://cf-manifest-audit-central-element-323112/cf_audit/2026-07-26.json`.
- [ ] [DATA] P2. Diagnose + fix Era-B (chain `data_type` in `{options_chain,futures_chain}`
      must be 0) RED on `market-data-tick-tradfi-prd` — contradicts the "already-confirmed"
      GREEN claim in `cross_cutting_manifest_canonicalisation_findings_2026_07_11.md`; re-verify
      that doc's tradfi Adjudication against this fresh evidence. Repo: market-tick-data-service.
- [ ] [DATA] P2. Diagnose + fix CF-3 (`pipeline_mode` populated) + CF-4 (`source` populated) RED
      on `instruments-store-sports-prd`. Repo: instruments-service (writer),
      unified-trading-library (audit tooling).
