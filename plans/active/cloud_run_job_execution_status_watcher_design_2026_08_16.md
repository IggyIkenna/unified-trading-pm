---
doc_type: plan
title: Fleet-wide Cloud Run Job execution-status watcher — design scoping
summary: >-
  No DP-* alert class or google_monitoring_alert_policy covers a generic Cloud Run JOB execution `Completed: False`
  (as opposed to a VM's `exit_code`, which DP-VM-001 already watches). This gap let `understat-eu-typing-sweep` OOM
  silently for 15 consecutive daily runs (2026-07-29..08-12) with zero page. This plan scopes the design of a
  fleet-wide Cloud Run Job execution-status watcher (mirroring DP-VM-001's exit_code-aware VM fleet monitor,
  generalized to `gcloud run jobs executions list`) before committing to a bounded AO-dispatchable implementation.
status: active
nature: design
asset_group: [meta]
stage: [meta]
repos: [deployment-service, unified-trading-pm]
scope: [engineer]
tags: [observability, cloud-run, data-pipeline-alerts, dp-vm-001, watcher, design]
related:
  [
    /plans/archive/issues/understat_eu_typing_sweep_daily_job_oom_2026_08_12.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/deployment-observability.md,
  ]
created: 2026-08-16
last_updated: 2026-08-16
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: design
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.9
assigned_role: infra
effort: low
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: understat_eu_typing_sweep_daily_job_oom_2026_08_12.md's [INFRA] P3 follow-up (filed 2026-08-12, scoped 2026-08-16)
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/data-pipeline-alerts.registry.yaml,
    deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py,
    deployment-service/deployment_service/data_pipeline_monitors/cli.py,
    /plans/archive/issues/understat_eu_typing_sweep_daily_job_oom_2026_08_12.md,
  ]
---

## Why this plan exists

Filed per the `[INFRA] P3` follow-up in
`/plans/archive/issues/understat_eu_typing_sweep_daily_job_oom_2026_08_12.md`'s own todo list: that issue's own DATA
todo confirmed (via `gcloud alpha monitoring policies list` + a grep of every `deployment-service/terraform/gcp/*monitor*`,
`*alert*` file) that **no failure-mode class in the registry watches a generic Cloud Run Job execution
`Completed: False`** — `DP-VM-001` is VM-fleet-specific (`run.log` terminal `exit_code`); `DP-CATALOG-001` only
catches a Cloud Run Job OOM indirectly, via that job's OUTPUT ARTIFACT freshness watcher, which most jobs don't have;
`DP-WATCHER-002` only proves the Cloud Scheduler TRIGGER fired, not that the downstream execution succeeded. The
`understat-eu-typing-sweep-daily` Cloud Scheduler job fired correctly every day for 15 consecutive days while its
Cloud Run Job execution OOM'd every single time — a silent production failure with zero page, caught only by an
operator's manual spot-check.

Building the real watcher is a cross-cutting infra design task (which target set? what's the freshness/staleness
signal? how does it avoid duplicating `DP-VM-001`'s VM-fleet mechanism?) — not a bounded fix, so it does not belong
folded into that issue doc. This plan is where that design gets resolved before any AO-dispatchable implementation
todo is written.

## Goal

Decide the concrete design for a fleet-wide Cloud Run Job execution-status watcher, generalizing `DP-VM-001`'s
exit-code-aware VM fleet monitor pattern (`deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py`,
invoked via `cli.py --mode exit-code`) to Cloud Run Jobs — then split the resolved design into a real AO-dispatchable
implementation plan (bounded, `assigned_vm: planning`, per the dispatch-scope-eligibility rule) once the open
questions below are answered.

## Design sketch (starting point, not yet a ruling)

- **Enumeration**: `gcloud run jobs list` (or the Cloud Run Admin API equivalent) across the fleet's Cloud Run Jobs —
  need to decide which jobs are in scope (all data-pipeline-owned jobs? every Cloud Run Job in the project? a
  registry like `LAUNCHER_FOR_VM_PREFIX` but for jobs?).
- **Per-job check**: `gcloud run jobs executions list --job=<job> --limit=N` (as the issue doc's own diagnosis used
  manually) — the watcher's job is to read each job's most recent execution(s) and classify `Completed: True` vs
  `Completed: False` vs "hasn't run in longer than its own schedule implies" (the `DP-WATCHER-002` cron-fired check,
  generalized).
- **New registry entry**: a `DP-VM-012`-or-similar id (category `VM` or a new `DP-JOB` category — decide which) in
  `/codex/05-infrastructure/data-pipeline-alerts.md` + `.registry.yaml`, mirroring the `DP-VM-001` row shape
  (`event`, `Detector`, `Escalation`, `Status`).
- **Escalation tier**: likely `page` (mirrors `DP-VM-001` non-OOM path) since a silently-failing daily job has no
  auto-recover actuator today — decide whether an `auto_recover` tier (e.g. resize-up on OOM, mirroring
  `relaunch_backfill_vm.py`'s VM-fleet actuator) is worth building for Cloud Run Jobs too, or whether `file_issue` +
  `page` is sufficient for v1.
- **Avoid duplicating `DP-VM-001`**: Cloud Run Jobs and backfill VMs are different compute primitives with different
  APIs (`gcloud run jobs executions list` vs the VM census + `run.log`/heartbeat blobs) — this watcher should NOT
  attempt to read VM-shaped signals for a Cloud Run Job, and should share only the alerting-registry/escalation
  plumbing, not the VM-specific detection code.

## Open questions to resolve before writing the AO-dispatchable implementation plan

- Scope: which Cloud Run Jobs are in scope for v1 — every data-pipeline-owned job (a bounded, enumerable set via
  `deployment-service/terraform/gcp/*.tf` job resources), or a project-wide `gcloud run jobs list`?
- Cadence: how often does the watcher poll — its own Cloud Scheduler cadence, or triggered by each job's own
  completion (Cloud Run Jobs execution-state change notifications, if that API exists)?
- Dedup: does this route through the existing `AlertDeduplicator`/`_RECURRING_ALERT_COOLDOWNS` map (per
  `/codex/05-infrastructure/data-pipeline-alerts.md`'s wiring-caveat section), same as the rest of the DP-* family?
- Does a `DP-JOB` category get its own id-block in the registry, or does this stay under `DP-VM` (the existing
  "VM lifecycle" category name would then be slightly misleading for a Cloud Run Job)?
- Actuator: is a v1 `file_issue`-only tier acceptable, or does the understat OOM history (repeatable, same root
  cause every day) justify an `auto_recover` actuator (e.g. resize-up-then-relaunch) from day one?

## Todos

- [ ] [INFRA] P3. Answer the open questions above (grep the terraform job inventory for the candidate job set; confirm
      whether a Cloud Run execution-state-change notification API exists; decide the registry id/category). Repo:
      unified-trading-pm (this doc) — record the ruling in this doc's Progress Log. Done when: every open question
      above has a decided answer with evidence, not a guess.
- [ ] [INFRA] P3. Once the design is resolved, author the real AO-dispatchable implementation plan (`assigned_vm:
      planning`, 10-100 todos per `task_template.md`) — split out of this LOCAL scoping doc, `depends_on` this plan's
      slug. Repo: unified-trading-pm. Done when: the new plan exists with `status: active` and this doc is updated to
      point at it (`entry_point_for`/`related`).

## Progress Log

- 2026-08-16 (slot 17, infra craft): Filed per the `[INFRA] P3` follow-up in
  `understat_eu_typing_sweep_daily_job_oom_2026_08_12.md`, which explicitly asked for this to be scoped as its own
  plan rather than folded into that issue. Classified as a LOCAL (`assigned_vm: NA`) plan per
  `task_template.md` § "Pick your track" — this is an open-ended design/judgment call (which target set, which
  cadence, which registry shape), not a worker-determinable bounded outcome, so it is not yet AO-eligible. Read the
  precedent (`exit_code_fleet_monitor.py`, the `DP-VM-001` registry row, the registry.yaml schema) and wrote the
  design sketch + open questions above; did not resolve them this pass (that is the first todo above, left open for
  whoever picks this up next — human or a future AO-dispatch once reclassified via `/na-eligibility-audit`).
