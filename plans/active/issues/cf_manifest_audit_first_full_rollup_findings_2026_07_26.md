---
doc_type: issue
title:
  First-ever complete CF-manifest-audit rollup (2026-07-26) — a false-positive checker bug (fixed) plus genuine cross-AG
  CF-8/Era-B/CF-3/CF-4 reds needing data-team triage
summary: >-
  The scheduled `uts-prod-cf-manifest-audit` Cloud Run Job had never completed a full run since it was created (14+
  consecutive daily OOM failures, root-caused + fixed in `cf_manifest_audit_scheduled_job_daily_failure_2026_07_13.md`).
  The first-ever complete 10-bucket rollup (2026-07-26,
  `gs://cf-manifest-audit-central-element-323112/cf_audit/2026-07-26.json`) surfaced two classes of finding: (1) a
  checker bug — CF-2-paths/CF-3-partition read RED on 10/10 buckets because `_probe_paths()`'s shallow descent always
  picked an irrelevant `_`-prefixed metadata/backup dir over real data (fixed same-session,
  `unified-trading-library@21069582`); (2) genuine, previously-invisible reds — CF-8 (`available_at`) is RED on 5 of 10
  buckets across 4 different asset_groups, and Era-B / CF-3 / CF-4 are RED on buckets a prior doc's Adjudication had
  marked "already-confirmed" GREEN. This doc tracks class (2) for data-team triage; class (1) is closed, cited for the
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
    /plans/archive/issues/cf_manifest_audit_scheduled_job_daily_failure_2026_07_13.md,
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
assigned_vm: planning
locked_by:
execution_scope: orchestrator-agent
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
---

# First complete CF-audit rollup — a fixed checker bug + genuine cross-AG data-quality reds

## Context

`uts-prod-cf-manifest-audit` never wrote a single successful daily output in its entire existence (see
`cf_manifest_audit_scheduled_job_daily_failure_2026_07_13.md`). Fixing the OOM (`unified-trading-library@6ce1ddb6` + a
Cloud Run memory bump to 32Gi/8vCPU, `deployment-service@e9bcb34`) let the job complete for the first time ever,
2026-07-26 21:14-21:18 UTC (execution `uts-prod-cf-manifest-audit-qsp6r`), writing
`gs://cf-manifest-audit-central-element-323112/cf_audit/2026-07-26.json`.

## Finding 1 — CF-2-paths/CF-3-partition false RED on 10/10 buckets (FIXED, cited for the record)

Every single sample path `_probe_paths()` returned was from an irrelevant top-level metadata/scratch dir
(`_migration_backup`, `_catalogue`, `_manifests`, `_cache`, `_legacy_migrated_processed`, `_audits`, `_backups`) — never
real `category=`/`asset_group=` hive-partitioned data. GCS `ls` returns lexicographic order and `_` sorts before
lowercase `a-z`, so `data_kids[0]` always preferred one of these over real data. **Fixed same-session**:
`unified-trading-library@21069582` generalizes the exclusion to "any top-level dir whose basename starts with `_`" with
5 regression tests reproducing the exact live pattern. Not yet visible in a live re-run — the MTDS image (which bundles
UTL) needs to pick up the new pin before the NEXT scheduled 06:00 UTC run reflects it. **Action**: re-check tomorrow's
run.

## Finding 2 — genuine reds needing data-team triage (NOT fixed here)

Full per-bucket rollup (excluding the Finding-1 false positives above):

| bucket                         | genuine reds                  |
| ------------------------------ | ----------------------------- |
| `market-data-tick-cefi-prd`    | CF-1, CF-3, CF-4, CF-8, Era-B |
| `instruments-store-cefi-prd`   | (clean)                       |
| `market-data-tick-defi-prd`    | (clean)                       |
| `instruments-store-defi-prd`   | (clean)                       |
| `market-data-tick-tradfi-prd`  | CF-8, Era-B                   |
| `instruments-store-tradfi-prd` | (clean)                       |
| `market-data-tick-sports-prd`  | CF-8                          |
| `instruments-store-sports-prd` | CF-3, CF-4, CF-8              |
| `market-data-tick-pred-prd`    | CF-8                          |
| `instruments-store-pred-prd`   | (clean)                       |

1. **cefi's CF-1/CF-4/CF-5/Era-B red is ALREADY a tracked todo** —
   `plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` "Bring cefi's raw_tick_data manifest to
   CF-1/CF-4/CF-5/Era-B GREEN" (source: `cross_cutting_manifest_canonicalisation_findings_2026_07_11.md`). This rollup
   is fresh confirming evidence — no new todo for cefi (note: cefi CF-3 red isn't in that todo's scope, fold it in when
   worked).
2. **CF-8 (`available_at`) RED on 4 of 5 asset_groups is NEW** — first evidence ever, since this check never ran to
   completion before. The source doc's "already-confirmed" GREEN language for tradfi/sports/prediction is contradicted
   here for CF-8 (and Era-B on tradfi, CF-3/CF-4 on sports/instruments-store). Only defi reads fully clean.

## Recommended decision

- [ ] [DATA] P2. Diagnose + fix CF-8 (`available_at` non-null coverage) RED on `market-data-tick-tradfi-prd`,
      `market-data-tick-sports-prd`, `instruments-store-sports-prd`, `market-data-tick-pred-prd` (cefi's CF-8 folds into
      the existing cefi todo above). Re-run `cf_manifest_audit.py` per-bucket after each fix. Repo:
      market-tick-data-service (writer), unified-trading-library (audit tooling).
- [ ] [DATA] P2. Diagnose + fix Era-B (chain `data_type` in `{options_chain,futures_chain}` must be 0) RED on
      `market-data-tick-tradfi-prd` — contradicts the "already-confirmed" GREEN claim in
      `cross_cutting_manifest_canonicalisation_findings_2026_07_11.md`; re-verify that doc's tradfi Adjudication against
      this fresh evidence. Repo: market-tick-data-service.
- [ ] [DATA] P2. Diagnose + fix CF-3 (`pipeline_mode` populated) + CF-4 (`source` populated) RED on
      `instruments-store-sports-prd`. Repo: instruments-service, unified-trading-library.
