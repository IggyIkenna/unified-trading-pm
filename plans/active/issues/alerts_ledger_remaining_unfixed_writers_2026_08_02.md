---
doc_type: issue
title: "Alerts ledger (cicd/alerts/) race closure incomplete -- 3 writers still do the unlocked read-modify-write"
summary: >-
  deployment_alerts_ingestion_completeness_2026_07_20.md (archived) fixed the alerts-ledger read-modify-write race for
  deployment-api's own writer and for the dedup axis, but explicitly left 2 other writers unfixed and closed anyway. A
  fresh grep-then-READ sweep (done incidentally while resolving ci_satellite_ao_dispatch_batch1-027's event-ledger-
  consumer todo) found a 3RD unfixed writer not enumerated in that archived plan: agent-orchestrator's own
  notifications/slack.py. All 3 share the identical shape already proven safe to fix (persist-event's own
  cp-down-append-cp-up -> single never-overwritten object migration, unified-trading-pm@4cbf2006d).
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ci-cd, github-actions, event-ledger, alerts-ledger, gcs, race-condition, silent-failure]
related:
  [
    /plans/archive/2026_07/deployment_alerts_ingestion_completeness_2026_07_20.md,
    /plans/archive/issues/persist_cicd_event_ledger_read_modify_write_race_2026_07_17.md,
    /plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
  ]
created: "2026-08-02"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
drift_direction: advance-code
assigned_role: infra
depends_on: []
locked_by:
resolved_by:
source: "incidental finding while resolving ci_satellite_ao_dispatch_batch1-027 (slot 7, infra, 2026-08-02)"
---

# Alerts ledger race closure incomplete

## What I found

`plans/archive/issues/persist_cicd_event_ledger_read_modify_write_race_2026_07_17.md`'s Resolution section fixed the
EVENTS ledger (`cicd/events/`) race by moving `.github/actions/persist-event/action.yml` from a shared
cp-down->append->cp-up `events.jsonl` to a single never-overwritten object per event (`unified-trading-pm@4cbf2006d`).
The sibling ALERTS ledger (`cicd/alerts/{date}/alerts.jsonl`, identical race shape) was only partially fixed:
`deployment_alerts_ingestion_completeness_2026_07_20.md` (now archived) fixed `deployment-api::_persist_alert()`'s own
writer the same way, but its own text says "two other writers into that same file (`notify-slack.yml`'s own persist
step, and `semver-agent.yml.tmpl`'s fleet-wide 'Persist CRITICAL pages' step) still do the old unlocked
read-modify-write and are NOT fixed by this pass" -- and the plan was archived with that gap still open, no active plan
currently owns finishing it.

A fresh grep-then-READ sweep found a **3rd, previously undocumented unfixed writer**:
`agent-orchestrator/server/notifications/slack.py::_persist_to_gcs()` (lines 127-169) does the identical
download-append-upload dance against `cicd/alerts/{date}/alerts.jsonl` (confirmed live, not from a stale citation).

## Why it matters

Per the archived race analysis: overlapping writers into the same shared object silently discard each other's rows while
every writer logs success. The alerts ledger backs `deployment-api`'s CI-alerts dashboard consumers (`GET /api/alerts`,
`deployment-ui`'s Alerts page) -- a lost alert row is a lost page/notification, not just lost telemetry. The archived
plan's own evidence showed this race directly caused a real incident (dedup fail-open -> noisiest alert class in
`#ci-failures`) before the dedup axis was separately fixed.

## Recommended decision

Apply the same proven, already-shipped fix (one never-overwritten object per write, mirroring
`unified-trading-pm@4cbf2006d`) to all 3 remaining writers:

## Todos

- [ ] [INFRA] P2. Fix `notify-slack.yml`'s own alerts-ledger persist step (the reusable workflow's inline
      cp-down/append/cp-up against `cicd/alerts/{date}/alerts.jsonl`) to write a single never-overwritten per-event
      object instead, mirroring `.github/actions/persist-event/action.yml`'s fix. (repo: unified-trading-pm)
- [ ] [INFRA] P2. Fix `semver-agent.yml.tmpl`'s fleet-wide "Persist CRITICAL pages" step the same way -- it is a
      TEMPLATE (`scripts/workflow-templates/semver-agent.yml.tmpl`), so the fix must land there + roll out via
      `rollout-workflow-templates.sh`, never hand-edited per-repo. (repo: unified-trading-pm)
- [ ] [INFRA] P2. Fix `agent-orchestrator/server/notifications/slack.py::_persist_to_gcs()` (lines 127-169) the same way
      -- replace the `download_from_storage` + string-append + `upload_to_storage` dance with a single never-overwritten
      object write (e.g. `cicd/alerts/{date}/{alert_class}-{nanosecond-timestamp}-{random}.jsonl`), confirming
      `deployment-api::_read_ledgers_sync()`'s existing prefix-walk over `cicd/alerts/` (already proven resilient to
      this shape for the events ledger) picks up the new per-file layout with no reader change needed. (repo:
      agent-orchestrator)

## Progress Log

- 2026-08-02 (slot 7, infra): filed as an incidental finding while resolving `ci_satellite_ao_dispatch_batch1-027` (the
  event-ledger-consumer audit). Did not fix inline -- out of that task's audit-only scope. No code changed this session
  for this doc.
