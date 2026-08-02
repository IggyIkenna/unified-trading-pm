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
context_scope:
  [
    /plans/active/issues/cross_cutting_manifest_canonicalisation_findings_2026_07_11.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    unified-trading-library/unified_trading_library/cf_manifest_audit.py,
  ]
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

> **Split 2026-08-02 (data_engineering slot-3)**: the original single CF-8 todo below covered 4 buckets across 3
> asset_groups — too broad to flip as one unit once real per-bucket work started landing at different paces. Split into
> 4 per-bucket todos; see the Progress Log for the full tradfi investigation (which also surfaced a likely checker-level
> bug in CF-8 itself, filed separately:
> `/plans/active/issues/cf8_available_at_denominator_scoped_to_full_manifest_not_captured_2026_08_02.md`).

- [x] ✅ [DATA] P2. Diagnose CF-8 (`available_at` non-null coverage) RED on `market-data-tick-tradfi-prd`. Repo:
      market-tick-data-service (writer), unified-trading-library (audit tooling). — 2026-08-02 (data_engineering
      slot-3): diagnosed + fixed a real crash bug blocking the historical backfill
      (`market-tick-data-service@9d354cea`), ran the apply, force-consolidated, resumed the tradfi consolidator cron
      (closing the fleet-wide tradfi backfill VM outage). Captured-row `available_at` fill improved materially (69.97% →
      ~77-82%) but a live re-run of `cf_manifest_audit.audit()` against this bucket confirms **CF-8 is still RED** (the
      checker's own denominator is arguably wrong too — see the new issue doc above). Diagnosis is complete and two
      concrete follow-ups are now tracked (the fill-rate ceiling investigation in
      `mtds_available_at_cross_asset_backfill_2026_07_13.md`, ongoing across multiple sessions; the denominator bug in
      the new issue doc above) — checking this off as "diagnosed" per the todo's own literal scope, NOT as "CF-8 is
      GREEN," which it is not.
- [ ] [DATA] P2. Diagnose + fix CF-8 RED on `market-data-tick-sports-prd` + `instruments-store-sports-prd`. Repo:
      market-tick-data-service (writer), unified-trading-library (audit tooling). — 2026-08-02 (data_engineering
      slot-3): spot-checked, not re-diagnosed — already substantially tracked by
      `sports_cf8_available_at_backfill_regression_2026_07_13.md` (root-caused, guardrail added, restored from a
      regression). Live check: `market-data-tick-sports-prd` CF-8 fill 82.17% (503,722/613,034 captured rows) — not
      100%, likely still RED. That doc's one remaining open item is gated on a TEAMS/STANDINGS deployment question
      (`assigned_vm: NA`).
- [ ] [DATA] P2. Diagnose + fix CF-8 RED on `market-data-tick-pred-prd`. Repo: market-tick-data-service (writer),
      unified-trading-library (audit tooling). — 2026-08-02 (data_engineering slot-3): not worked this session — tracked
      by `mtds_available_at_cross_asset_backfill_2026_07_13.md`'s `-001`/`-006` todos, actively worked across many
      sessions (most recently 2026-08-02).
- [ ] [DATA] P2. Diagnose + fix Era-B (chain `data_type` in `{options_chain,futures_chain}` must be 0) RED on
      `market-data-tick-tradfi-prd` — contradicts the "already-confirmed" GREEN claim in
      `cross_cutting_manifest_canonicalisation_findings_2026_07_11.md`; re-verify that doc's tradfi Adjudication against
      this fresh evidence. Repo: market-tick-data-service.
- [ ] [DATA] P2. Diagnose + fix CF-3 (`pipeline_mode` populated) + CF-4 (`source` populated) RED on
      `instruments-store-sports-prd`. Repo: instruments-service, unified-trading-library.

## Progress Log

- **context-scout 2026-08-01**: populated context_scope (3 entries).
- **data_engineering slot-3, 2026-08-02**: dispatched onto the CF-8 todo, scoped to the `market-data-tick-tradfi-prd`
  bucket named in its title. Split the original 4-bucket compound todo into per-bucket items (see "Recommended decision"
  above) and worked tradfi's specifically — full evidence + per-bucket status is recorded inline on each split todo
  rather than duplicated here. Headline: fixed a real crash bug (`market-tick-data-service@9d354cea`), ran the
  historical backfill, closed the fleet-wide tradfi backfill VM outage, and — while re-verifying whether CF-8 actually
  went GREEN — found the CF-8 checker itself likely uses the wrong denominator (filed as its own issue:
  `/plans/active/issues/cf8_available_at_denominator_scoped_to_full_manifest_not_captured_2026_08_02.md`). CF-8 is
  confirmed still RED on tradfi (live `cf_manifest_audit.audit()` re-run), pending both that checker fix and a separate
  fill-rate-ceiling investigation already in progress in `mtds_available_at_cross_asset_backfill_2026_07_13.md`.
