---
doc_type: issue
title: Multiple deployment-service consolidator watchers/registries assume the WRONG Cloud Run job-name scheme
summary: >-
  DP-MANIFEST-001 escalation agt-d1be49 (2026-08-15, tradfi CONSOLIDATOR_DOWN) traced back to
  `scripts/recovery/relaunch_consolidator.py::job_name()` building `manifest-consolidator-{asset_group}` — a name that
  has NEVER existed in GCP. The real per-(service_kind, asset_group) job is
  `uts-prod-manifest-consolidator-{instruments|market-data}-{asset_group}` (confirmed live via `gcloud run jobs list`;
  terraform/gcp/manifest_consolidator_scheduler.tf `manifest_consolidator_buckets` local's key is
  `"{service_kind}-{asset_group}"`, job name `"${local.env_prefix}-manifest-consolidator-${each.key}"`). Every REAL
  (non-dry-run) invocation of the actuator therefore 404'd — this fix (relaunch_consolidator.py + escalation.py's
  `_recover_consolidator`, now resolves service_kind from `finding.details["bucket"]`) is shipped in this same session.
  The SAME wrong `manifest-consolidator-{ag}` stem (one entry per asset_group, 5 total, vs the real 10 env-tiered jobs)
  is still baked into THREE more places that were NOT touched by this fix because they are a separate, larger surface:
  `deployment_service/cloud_run_job_registry.py::_MANIFEST_CONSOLIDATOR_JOBS` (the classified-inventory SSOT feeding
  deployment-observability/deployment-ui + DP-WATCHER-006's `CLOUD_RUN_JOBS` failure-detection scan — meaning
  DP-WATCHER-006 never watches the real per-kind consolidator jobs, only 5 nonexistent stems),
  `deployment_service/data_pipeline_monitors/consolidator_oom_watcher.py` (DP-WATCHER-005 OOM detector, docstring/log
  lines reference the same wrong per-AG family — reads Cloud Run execution history "for each per-AG
  `manifest-consolidator-{ag}` Cloud Run Job"), and
  `deployment_service/data_pipeline_monitors/cloud_run_job_failure_watcher.py` (DP-WATCHER-006, excludes
  `manifest-consolidator-*` stem prefix assuming DP-WATCHER-005 already covers it — it does not, for the same reason).
  Net effect: the 10 real `uts-prod-manifest-consolidator-{kind}-{ag}` jobs are NOT covered by either OOM detection
  (DP-WATCHER-005) or generic failure detection (DP-WATCHER-006) — a genuine execution failure on any of them currently
  produces NO alert via either watcher (DP-MANIFEST-001's heartbeat-staleness watcher is the only thing that still
  catches it, and only after the heartbeat budget is exceeded).
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags:
  [
    deployment-service,
    data-pipeline-monitors,
    manifest-consolidator,
    cloud-run,
    job-registry,
    alerting-gap,
    dp-manifest-001,
    dp-watcher-005,
    dp-watcher-006,
  ]
related: [/codex/05-infrastructure/manifest-consolidator-ssot.md, /codex/05-infrastructure/data-pipeline-alerts.md]
created: "2026-08-15"
author: data_pipeline_failure-agent (escalation agt-d1be49, slot 18)
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
priority: P1
drift_direction: advance-code
source: [escalation-agt-d1be49]
resolved_by:
locked_by:
locked_since:
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    deployment-service/deployment_service/cloud_run_job_registry.py,
    deployment-service/deployment_service/data_pipeline_monitors/consolidator_oom_watcher.py,
    deployment-service/deployment_service/data_pipeline_monitors/cloud_run_job_failure_watcher.py,
    deployment-service/scripts/recovery/relaunch_consolidator.py,
    deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf,
  ]
---

# What

Three deployment-service files still encode the job-name stem `manifest-consolidator-{ag}` (one per asset_group, 5
total) instead of the real live GCP naming, `uts-prod-manifest-consolidator-{service_kind}-{ag}` (one per (service_kind,
asset_group) pair — `instruments` + `market-data`, 10 env-tiered jobs; `features`/`strategy`/`execution` etc. also exist
under `manifest_consolidator_buckets_extended`). This is the SAME root defect this session's DP-MANIFEST-001 fix
corrected in `relaunch_consolidator.py` — those three are a separate blast radius not required to unblock that relaunch,
so they were left as a follow-up rather than expanded in-scope for a one-shot escalation.

# Why it matters

- `cloud_run_job_registry.py::_MANIFEST_CONSOLIDATOR_JOBS` only registers 5 stems that don't exist live — the
  deployment-observability surface (deployment-api `/api/deployments`, deployment-ui Deployments page) is blind to the
  real 10+ consolidator jobs.
- `cloud_run_job_failure_watcher.py` (DP-WATCHER-006) reads `CLOUD_RUN_JOBS` from that same registry and explicitly
  EXCLUDES anything matching the `manifest-consolidator-*` stem, on the stated assumption DP-WATCHER-005 already covers
  it.
- `consolidator_oom_watcher.py` (DP-WATCHER-005) is the one that's SUPPOSED to cover it, but its own docstring/log lines
  target the same nonexistent per-AG family — needs verification against its actual Cloud Run execution-history read
  path (does it use the registry, or resolve names correctly some other way? not yet checked in this session).
- Net: possible alerting BLIND SPOT for genuine consolidator execution failures on the real per-kind jobs, caught only
  by the slower heartbeat-staleness path (DP-MANIFEST-001, budget=300s+consecutive-miss gate) rather than immediate
  per-execution failure detection.

# Recommended decision

1. Read `consolidator_oom_watcher.py` in full to determine whether it actually queries Cloud Run by the WRONG name (a
   live gap) or resolves the job list some other way (already correct, only the docstring is stale).
2. Fix `cloud_run_job_registry.py::_MANIFEST_CONSOLIDATOR_JOBS` to emit the real `{service_kind}-{ag}` stems (10
   entries, or read `manifest_consolidator_buckets`'s keys directly from terraform-parity rather than hand-listing) —
   run `tests/unit/test_cloud_run_job_registry_guard.py` after, it parses `*_scheduler.tf` and should catch drift.
3. Re-verify `cloud_run_job_failure_watcher.py`'s exclusion list + `consolidator_oom_watcher.py`'s read path against the
   corrected registry; confirm the real per-kind jobs are covered by exactly one of the two watchers, not zero.
4. Grep for any other `manifest-consolidator-{ag}` / `manifest-consolidator-{asset_group}` literal across
   deployment-service beyond the four files already found (`relaunch_consolidator.py` docstrings fixed this session,
   `cloud_run_job_registry.py`, `consolidator_oom_watcher.py`, `cloud_run_job_failure_watcher.py`).

# Progress Log

- 2026-08-15 (agt-d1be49, slot 18): filed during DP-MANIFEST-001 tradfi escalation triage; root cause fixed in
  `relaunch_consolidator.py` + `escalation.py` in the same session (shipped separately), this doc tracks the remaining
  three-file blast radius.
- **context-scout 2026-08-17**: populated context_scope (6 entries).
