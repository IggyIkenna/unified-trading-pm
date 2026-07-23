---
doc_type: issue
title:
  Scheduled `uts-prod-cf-manifest-audit` Cloud Run Job (CF-1..CF-14 manifest audit, all 5 asset_groups, daily 06:00 UTC)
  has never successfully produced output — failing every day 2026-07-04 through 2026-07-13, today's run OOM'd
summary:
  "Found 2026-07-13 while recording the first-ever post-apply cefi CF-1..CF-14 manifest audit into
  `data_completion_to_100_all_ag_2026_06_21.md` (that audit had to be run MANUALLY this session because the automated
  daily job has never worked). The scheduled Cloud Run Job `uts-prod-cf-manifest-audit` (asia-northeast1) is supposed to
  run `unified-trading-library/unified_trading_library/cf_manifest_audit.py` for ALL 5 asset_groups
  (cefi/defi/tradfi/sports/prediction) once a day at 06:00 UTC. Checked its execution history: it has failed EVERY DAY
  from 2026-07-04 through 2026-07-13 inclusive — most days 'Application exec likely failed' (container exit 1); TODAY's
  run specifically hit an OOM (container reached its configured 4Gi memory limit) on the `--all-ags` single-container
  invocation. Its designated output location `gs://cf-manifest-audit-central-element-323112/cf_audit/` has 0 objects —
  confirming zero successful runs in this window, not just a logging gap. This is a cross-cutting infra gap (affects
  cefi/defi/tradfi/sports/prediction equally — none of the 5 asset_groups get a daily automated CF-audit today; every
  CF-audit reading anyone has used this session was a manual one-off run). Likely fix is either (a) bump the Cloud Run
  Job's memory limit above 4Gi (the `--all-ags` single-container pass over 5 asset_groups' full manifests is
  memory-heavy), or (b) split the job into 5 per-asset_group Cloud Run executions instead of one `--all-ags` container,
  mirroring the per-AG pattern already used by the manifest consolidator jobs. Not attempted or fixed in this pass — is
  its own dedicated infra task, reported here per the big-finding / cross-cutting NOTIFY-OPERATOR rule rather than
  silently worked around."
status: open
nature: notes
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-library, deployment-service]
scope: [engineer, admin]
tags:
  [
    cf-manifest-audit,
    cloud-run,
    scheduled-job,
    oom,
    cross-cutting,
    data-correctness,
    cefi,
    defi,
    tradfi,
    sports,
    prediction,
  ]
related:
  [
    ../data_completion_to_100_all_ag_2026_06_21.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: 2026-07-13
parent_epic: mtds_mdps_master
priority: P1
source:
  [
    cefi CF-audit recording pass 2026-07-13 (this session),
    Cloud Run execution history for uts-prod-cf-manifest-audit,
    gs://cf-manifest-audit-central-element-323112/cf_audit/ (0 objects),
  ]
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
---

# `uts-prod-cf-manifest-audit` scheduled job — daily failure since 2026-07-04, zero successful runs

## Context

`unified-trading-library/unified_trading_library/cf_manifest_audit.py` implements the CF-1..CF-14 canonical-form
manifest audit used throughout `data_completion_to_100_all_ag_2026_06_21.md` to gate legacy-bucket decommission and
manifest canonicalisation work. It is meant to run automatically, once a day, for ALL 5 asset_groups, via the scheduled
Cloud Run Job `uts-prod-cf-manifest-audit` (asia-northeast1, cron 06:00 UTC).

## What was found (real evidence, not inference)

1. **Zero successful runs in the checked window.** Execution history for `uts-prod-cf-manifest-audit` shows failures on
   every day from 2026-07-04 through 2026-07-13 (10 consecutive days). Most days: "Application exec likely failed"
   (container exit 1, no further detail surfaced in the execution summary). Today (2026-07-13) specifically: OOM — the
   container hit its configured memory limit (4Gi) on the `--all-ags` invocation.
2. **Output bucket confirms zero completions, not a logging blind spot.**
   `gs://cf-manifest-audit-central-element-323112/cf_audit/` has 0 objects. If any run had completed successfully at any
   point in this window, an audit-result object would exist there.
3. **Practical consequence surfaced this session**: the first-ever post-apply cefi CF-1..CF-14 audit had to be run
   MANUALLY (a prior verified investigation this session executed `cf_manifest_audit.py` directly against live cefi
   data) precisely because the automated daily pipeline that is supposed to produce this for every asset_group has never
   produced anything in this window. Every CF-audit number cited anywhere in the plan for any asset_group this session
   traces back to a manual one-off run, not the scheduled job.
4. **Cross-cutting, not cefi-specific.** The job runs `--all-ags` in one container — the same failure/OOM affects
   cefi/defi/tradfi/sports/prediction equally. None of the 5 asset_groups currently get a daily automated CF-audit.

## Likely fix (not attempted this pass)

- (a) Bump the Cloud Run Job's memory limit above 4Gi for the `--all-ags` invocation, and/or
- (b) Split into 5 per-asset_group Cloud Run executions (mirrors the per-AG pattern the manifest consolidator jobs
  already use) instead of one `--all-ags` single-container pass — likely the more robust fix since it also gives per-AG
  failure isolation (today's finding is that a single AG's audit is already memory-heavy at scale).

## Why this is reported, not fixed

This is genuinely its own scoped infra task (job config change + redeploy + a verified first-green run, evidence-backed
per the `Evidence: cloudbuild=<id>` rule) — out of scope for the cefi recording pass that surfaced it. Flagged per the
CLAUDE.md big-finding / cross-cutting NOTIFY-OPERATOR rule rather than silently worked around or left undocumented.

## Next steps (not yet started)

- [ ] [INFRA] P1. Diagnose the exact exit-1 cause on the non-OOM failure days (2026-07-04 through 2026-07-12) via
      `gh`/`gcloud run jobs executions describe` + `--log-failed`-equivalent Cloud Logging query — confirm whether they
      are the same OOM under a different symptom or a distinct bug.
- [ ] [INFRA] P1. Either bump the job's memory limit (measure the real peak RSS for a full `--all-ags` pass first) or
      split into 5 per-asset_group Cloud Run executions/schedules.
- [ ] [INFRA] P1. Verify with a real green run: `gs://cf-manifest-audit-central-element-323112/cf_audit/` gains a fresh
      dated object for all 5 asset_groups after the fix, cited with resolving evidence.
