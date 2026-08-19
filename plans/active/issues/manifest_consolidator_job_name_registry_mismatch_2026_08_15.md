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
asset_group:
  [cross-cutting] # corrected 2026-08-19 (ag-closeout-audit cross-cutting tranche, meta-sweep) -- was [meta]; content
  # is manifest-consolidator Cloud Run job-name registry/monitoring drift spanning multiple asset groups
  # (instruments/market-data consolidator jobs, DP-WATCHER-005/006 alerting gap) -- squarely cross-cutting
  # data-pipeline scope per /codex/05-infrastructure/manifest-consolidator-ssot.md, not a generic process-level doc.
  # Already self-dispatched (assigned_vm: planning, status: open) so this retag does not create a new orphan.
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

## Todos

**Added 2026-08-19 (plan-reconcile observability_master, Phase 2 zero-checkbox sweep)** — this P1 doc with confirmed
LIVE production harm (13+ hour cefi consolidator outage, growing tradfi stall — see Progress Log) had zero `- [ ]`
tracked work, invisible to the AO backlog (`regen_backlog_from_plan.py` only parses checkbox lines). Converted the
4-item "Recommended decision" list above into tracked todos verbatim — same content, same order, now dispatchable.

- [x] ✅ [INFRA] P1. Read `deployment_service/data_pipeline_monitors/consolidator_oom_watcher.py` in full to determine
      whether it actually queries Cloud Run by the WRONG `manifest-consolidator-{ag}` name (a live gap) or resolves
      the job list some other way (already correct, only the docstring/log lines are stale). Done when: a stated
      verdict (live gap vs. docstring-only) with the specific code path cited as evidence. Repo: deployment-service.
      — deployment-service (see Progress Log 2026-08-19, slot 31).
- [x] ✅ [INFRA] P1. Fix `deployment_service/cloud_run_job_registry.py::_MANIFEST_CONSOLIDATOR_JOBS` to emit the real
      `uts-prod-manifest-consolidator-{service_kind}-{ag}` stems (10 entries across `instruments`/`market-data`, or
      read `manifest_consolidator_buckets`'s keys directly from terraform-parity rather than hand-listing). Done
      when: `tests/unit/test_cloud_run_job_registry_guard.py` passes (it parses `*_scheduler.tf` and should catch
      drift) + `quality-gates.sh` green. Repo: deployment-service.
      — deployment-service@a0005a5539 (see Progress Log 2026-08-19, slot 14).
- [ ] [INFRA] P1. Re-verify `deployment_service/data_pipeline_monitors/cloud_run_job_failure_watcher.py`'s
      `manifest-consolidator-*` exclusion list + `consolidator_oom_watcher.py`'s read path against the registry
      fixed in the todo above; confirm the real per-(service_kind, asset_group) jobs are covered by exactly one of
      the two watchers, not zero. Done when: a stated coverage verdict per real job stem, evidenced by reading both
      watchers' current logic against the corrected registry. Repo: deployment-service.
- [ ] [INFRA] P2. Grep deployment-service for any other `manifest-consolidator-{ag}` / `manifest-consolidator-
      {asset_group}` literal beyond the four files already found (`relaunch_consolidator.py` docstrings fixed
      2026-08-15, `cloud_run_job_registry.py`, `consolidator_oom_watcher.py`, `cloud_run_job_failure_watcher.py`).
      Done when: grep output pasted + any additional hit either fixed or explicitly ruled a non-issue. Repo:
      deployment-service.

# Progress Log

- 2026-08-15 (agt-d1be49, slot 18): filed during DP-MANIFEST-001 tradfi escalation triage; root cause fixed in
  `relaunch_consolidator.py` + `escalation.py` in the same session (shipped separately), this doc tracks the remaining
  three-file blast radius.
- **context-scout 2026-08-17**: populated context_scope (6 entries).
- **data_pipeline_alerts_reconciler 2026-08-17 (slot 28, dispatch agt-e28b69)**: 6-hourly channel-reconciliation sweep
  found LIVE evidence this gap is causing ongoing production harm today, not just a theoretical blind spot. Neither
  condition below reached `#data-pipeline-alerts` (by design — `consolidator_rules.py` routes `CONSOLIDATOR_DOWN`/
  `MANIFEST_CONSOLIDATION_STALLED` to PagerDuty+Telegram only, no Slack mirror — so Slack silence on this specific
  gap is expected, not itself a bug; flagged here because "channel quiet" would otherwise read as "fleet healthy").
  `gcloud logging read` against `dp-alerting-subscriber`'s own ERROR-severity logs (ground truth, not Slack):
  - `Consolidator DOWN for bucket=market-data-tick-cefi-prd-central-element-323112 heartbeat_age_sec=47326.6` at
    `12:20:18Z`, climbing from `41949.1` at `10:50:20Z` — i.e. STILL down, continuously, for 13+ hours as of this
    sweep, not a transient blip.
  - `Manifest consolidation STALLED for bucket=market-data-tick-tradfi-prd-central-element-323112 streak=14
    shards_scanned=560 baseline_shards=157` at `11:44:18Z`, climbing from `streak=10` at `11:28:12Z` — shards keep
    landing but no cycle has merged them, ongoing.
  - One anomalous `Consolidator DOWN for bucket=unknown heartbeat_age_sec=None` at `11:06:05Z` — bucket resolution
    itself failed for that single fire; not chased further (single occurrence, did not recur in the 2h window
    checked), possibly a transient blip during ambient VM churn rather than this doc's registry-name bug specifically.
  Not independently re-diagnosed against this doc's specific job-name-mismatch root cause this sweep (proportionate
  scope for a one-shot channel-reconciliation dispatch) — appending as corroborating live evidence that the 3-file
  watcher/registry gap this doc already tracks is presently allowing a real, multi-hour CeFi outage + a growing
  tradfi stall to run with only the slow heartbeat-staleness path (which itself paged PagerDuty/Telegram, not Slack)
  catching it. Given `assigned_vm: planning` is already set, no reclassification needed — flagging for priority
  given the live-incident evidence now attached, and per the "data pipeline correctness is the heartbeat" HARD RULE.
- **2026-08-19 (slot 31, todo 1 — infra)**: Read `consolidator_oom_watcher.py` in full. **Verdict: LIVE GAP, not just a
  stale docstring** — and a DIFFERENT bug than this doc's own hypothesis (it isn't the `manifest-consolidator-{ag}`
  missing-kind/missing-env-prefix stem from `cloud_run_job_registry.py`; it's a missing separator). Evidence:
  `make_consolidator_execution_oom_reader`'s `_read()` built
  `job_name = f"{env_prefix}manifest-consolidator-market-data-{ag}"` (no hyphen between `env_prefix` and the stem)
  when called with `env_prefix=_scheduler_env_prefix()` (`cli.py:823-824`), and `scheduler_env_prefix()` returns the
  BARE prefix `"uts-{environment}"` with no trailing hyphen (`meta_targets.py:158-174`, e.g. `"uts-prod"`) — every
  OTHER caller in this codebase that combines the two inserts the hyphen explicitly
  (`meta_targets.consolidator_cloud_run_job`: `f"{scheduler_env_prefix()}-manifest-consolidator-market-data-{ag}"`;
  `cloud_run_job_failure_watcher.make_job_execution_reader`'s `_read()` and `stale_image_watcher.make_image_digest_reader`'s
  `_read()` both do `f"{env_prefix}-{job_stem}"`). So this reader queried `uts-prodmanifest-consolidator-market-data-{ag}`
  — a job name that has never existed — meaning `executions_client.list_executions(parent=...)` 404s/errors on every
  call, `oom_diagnostics.get(ag)` is always `None`, and DP-WATCHER-005 can never classify an OOM for ANY asset_group,
  regardless of the registry fix in todo 2. **Fixed in the same commit** (findings-triage "in your file → fix in same
  commit"): inserted the missing hyphen (now matches the sibling readers' pattern), corrected the stale module
  docstring (line ~11, previously said bare `manifest-consolidator-{ag}`) and the emitted-finding `summary` f-string
  (previously the same bare stem) to the real `market-data`-kind name shape, and added
  `tests/unit/test_consolidator_oom_watcher.py` (2 tests) asserting the `parent` path built with/without an
  `env_prefix` — locks in the fix so it can't silently regress. **Residual, NOT fixed here (relevant to todo 3's
  re-verification)**: this reader is hardcoded to the `market-data` kind only (`f"...-market-data-{ag}"`) — it has no
  `instruments`-kind branch (unlike `relaunch_consolidator.py`'s `kind_for_bucket`/`job_name(kind=...)`), so even with
  the hyphen fixed, DP-WATCHER-005 still only ever covers the 5 `market-data` consolidator jobs, never the 5
  `instruments` ones — todo 3 should confirm whether those are covered by DP-WATCHER-006 or remain a real gap. Shipped:
  deployment-service (see commit in slot 31's `/done` evidence).
- **2026-08-19 (slot 14, todo 2 — infra)**: Fixed `cloud_run_job_registry.py::_MANIFEST_CONSOLIDATOR_JOBS`. It hand-listed
  5 stems (`manifest-consolidator-{ag}`, one per asset_group) which have never existed live — replaced with the real
  10 `manifest-consolidator-{kind}-{ag}` stems (`kind` in `instruments`/`market-data` × the 5 asset_groups), matching
  `manifest_consolidator_scheduler.tf`'s `manifest_consolidator_buckets` `for_each` map (`each.key` = `"{kind}-{ag}"`).
  Also corrected the module docstring's stale `manifest-consolidator-{ag}` example. Verified:
  `tests/unit/test_cloud_run_job_registry_guard.py` (10/10 passed — the tf-stem-coverage guard now matches the real
  names instead of passing by substring-luck against the old wrong stems), `tests/unit/test_dp_recovery_actuators.py` +
  `tests/unit/test_consolidator_oom_watcher.py` (82 passed, unaffected), full `quality-gates.sh` green. Did NOT touch
  `cloud_run_job_failure_watcher.py`'s exclusion list or `consolidator_oom_watcher.py`'s read path — that's todo 3's
  scope (this fix changes what jobs the registry NAMES, not which watcher classifies them). Shipped:
  deployment-service@a0005a5539.
