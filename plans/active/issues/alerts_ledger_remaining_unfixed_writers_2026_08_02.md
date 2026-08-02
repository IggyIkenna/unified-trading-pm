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
status: resolved
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
  slot-15 (todo 1, 2026-08-02, already fixed unified-trading-pm@363e8a7cc), slot-7 (todos 2-3, 2026-08-02) --
  unified-trading-pm@963daa611 (todo 2, already fixed) and agent-orchestrator@80cb301 (todo 3, genuine fix)
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

- [x] ✅ [INFRA] P2. Fix `notify-slack.yml`'s own alerts-ledger persist step (the reusable workflow's inline
      cp-down/append/cp-up against `cicd/alerts/{date}/alerts.jsonl`) to write a single never-overwritten per-event
      object instead, mirroring `.github/actions/persist-event/action.yml`'s fix. (repo: unified-trading-pm) — **ALREADY
      FIXED, no code change needed** (verified 2026-08-02). This todo's own claim was STALE: it cites
      `deployment_alerts_ingestion_completeness_2026_07_20.md`'s archived text verbatim ("notify-slack.yml's own persist
      step... still do the old unlocked read-modify-write") without re-checking the live file — a grep-then-conclude
      miss. `git log -- .github/workflows/notify-slack.yml` shows `unified-trading-pm@363e8a7cc` ("notify-slack.yml
      writes one alert object per call instead of shared alerts.jsonl") already shipped this EXACT fix on 2026-07-21 —
      12 days before this issue doc was filed (2026-08-02) and confirmed still live/unreverted (no later commit touches
      this file). The current persist step (lines ~449-464) writes `cicd/alerts/${DATE_PARTITION}/${UNIQUE_KEY}.jsonl`
      per alert (never a shared cp-down/append/cp-up), byte-for-byte the pattern this todo asked for. (The separate
      `scripts/self-hosted-runners/hosted-baseline/notify-slack.yml` copy is an intentionally-frozen self-hosted-
      runner-migration REVERT-PATH template, not a live-executed workflow — its drift from the active file is an
      already-tracked, unrelated concern, e.g. `plans/active/june_2026_vintage_audit_findings_2026_07_27.md`.)
- [x] ✅ [INFRA] P2. Fix `semver-agent.yml.tmpl`'s fleet-wide "Persist CRITICAL pages" step the same way -- it is a
      TEMPLATE (`scripts/workflow-templates/semver-agent.yml.tmpl`), so the fix must land there + roll out via
      `rollout-workflow-templates.sh`, never hand-edited per-repo. (repo: unified-trading-pm) — **ALREADY FIXED, no code
      change needed** (verified 2026-08-02, slot 7). Same stale-citation pattern as todo 1: this issue doc's body
      inherited `deployment_alerts_ingestion_completeness_2026_07_20.md`'s original unfixed-writers claim without
      re-checking that a LATER doc (`plans/archive/issues/alerts_ledger_race_two_remaining_writers_2026_07_21.md`,
      `status: resolved`) already closed exactly this gap on 2026-07-21: `unified-trading-pm@963daa611` rewrote the
      template's "Persist CRITICAL pages to alert ledger" step to write each run's queued pages to a unique
      `cicd/alerts/${DATE_PARTITION}/${UNIQUE_KEY}.jsonl` object (never a shared cp-down/append/cp-up), then
      `rollout-workflow-templates.sh` propagated the rendered `.github/workflows/semver-agent.yml` to all 24 service
      repos the same day (each committed+pushed individually — shas listed in that resolved issue doc). Verified live
      2026-08-02: the fix is present in the current template
      (`scripts/workflow-templates/semver-agent.yml.tmpl:918-943`, comment cites the exact 2026-07-21 issue doc) and
      spot-checked still live/unreverted in 4 rendered per-repo copies (instruments-service, market-tick-data-service,
      agent-orchestrator, deployment-api — `.github/workflows/semver-agent.yml`), no later commit touches the
      persist-step in any of them.
- [x] ✅ [INFRA] P2. Fix `agent-orchestrator/server/notifications/slack.py::_persist_to_gcs()` (lines 127-169) the same
      way -- replace the `download_from_storage` + string-append + `upload_to_storage` dance with a single
      never-overwritten object write (e.g. `cicd/alerts/{date}/{alert_class}-{nanosecond-timestamp}-{random}.jsonl`),
      confirming `deployment-api::_read_ledgers_sync()`'s existing prefix-walk over `cicd/alerts/` (already proven
      resilient to this shape for the events ledger) picks up the new per-file layout with no reader change needed.
      (repo: agent-orchestrator) — **agent-orchestrator@80cb301**. Unlike todos 1-2, this one WAS genuinely still
      broken: confirmed live at `server/notifications/slack.py::_persist_to_gcs()` before touching anything (per craft
      north-star + both prior todos' stale-citation precedent) — it still did the unlocked `download_from_storage` +
      string-append + `upload_to_storage` read-modify-write onto the shared `cicd/alerts/{date}/alerts.jsonl`. Fixed to
      mirror the proven pattern (deployment-api's `_persist_alert()`, `semver-agent.yml.tmpl`, both 2026-07-21): each
      alert now writes straight to its own never-overwritten `cicd/alerts/{date}/{uuid4().hex}.jsonl` object, no read/
      merge/lock. `deployment-api::_read_ledgers_sync()`'s existing prefix-walk needs no reader change. QG-verified:
      full `quality-gates.sh` green (2239 passed, 2 skipped, 0 basedpyright errors) before shipping; existing
      `_persist_to_gcs` tests (`test_slack_notifications.py`, `test_alert_quality_overhaul.py`) all mock at the function
      boundary so the internal-implementation change is untested-but-covered by the function-level mocks (no test
      asserted the old download/append internals). Verified SHA on origin before this flip.

## Progress Log

- **2026-08-02 (slot 15, infra)**: dispatched todo 1 only (`notify-slack.yml`). Read the LIVE
  `.github/workflows/notify-slack.yml` before implementing (per craft north-star — never launch/patch blind) and found
  the described race is already gone: `unified-trading-pm@363e8a7cc` (2026-07-21) already rewrote the persist step to
  one never-overwritten object per alert. This todo's summary/body inherited the archived
  `deployment_alerts_ingestion_completeness_2026_07_20.md`'s stale unfixed-writers list without re-verifying current
  code. Flipped todo 1 with the evidence; did NOT touch todos 2/3 (semver-agent.yml.tmpl, agent-orchestrator's slack.py)
  — out of this task's scope, and not independently re-verified as still-broken or already-fixed. A worker picking
  either of those up should do the same live-file check first, given todo 1 turned out stale.

- 2026-08-02 (slot 7, infra): filed as an incidental finding while resolving `ci_satellite_ao_dispatch_batch1-027` (the
  event-ledger-consumer audit). Did not fix inline -- out of that task's audit-only scope. No code changed this session
  for this doc.

- 2026-08-02 (slot 7, infra): dispatched todo 2 (`semver-agent.yml.tmpl`). Per craft north-star + the precedent set by
  todo 1 (also stale), read the LIVE template before implementing and found the fix already shipped:
  `unified-trading-pm@963daa611` (2026-07-21) + a same-day `rollout-workflow-templates.sh` propagation to all 24 service
  repos, tracked in the now-`resolved` `alerts_ledger_race_two_remaining_writers_2026_07_21.md`. This issue doc's own
  body cites only the ORIGINAL `deployment_alerts_ingestion_completeness_2026_07_20.md` gap and never cross-referenced
  the later doc that closed it. Flipped todo 2 with evidence; did not touch todo 3
  (`agent-orchestrator/server/notifications/slack.py`) -- out of scope, not independently re-verified. A worker picking
  it up should do the same live-file check first, given both prior todos in this doc turned out stale.

- 2026-08-02 (slot 7, infra): dispatched todo 3 (`agent-orchestrator/server/notifications/slack.py::_persist_to_gcs()`).
  Read the LIVE function first (both priors were stale) -- this time it WAS genuinely still broken: the unlocked
  download-append-upload race, unfixed. Fixed to mirror the proven one-object-per-write pattern, shipped
  `agent-orchestrator@80cb301` (full `quality-gates.sh` green: 2239 passed, 0 basedpyright errors), verified SHA on
  origin, flipped the checkbox. All 3 todos in this doc are now done -- flipping `status` to `resolved`.
