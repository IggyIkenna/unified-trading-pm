---
doc_type: issue
title: >-
  Escalation-dispatch dedup (Option A) is inert in production — the fleet-monitor host has no PM clone, so
  `_resolve_pm_path` returns None and every DP_RUN_MOSTLY_EMPTY re-page (including STATIC BACKLOG) still full-dispatches
  a fresh data_pipeline_failure worker
summary: >-
  The Option A escalation-dispatch dedup shipped in deployment-service@1b035c52 + @9102eb9b gates the
  DP_RUN_MOSTLY_EMPTY fast-spawn on a checkpoint stored on a local unified-trading-pm clone (escalation_dedup.py
  `check_dispatch_dedup`, reached via escalation.py `_resolve_pm_path`). But the fleet monitor runs as a Cloud Run job
  on the deployment-api image, which carries NO PM clone: cloudbuild.yaml explicitly empties `pm-plans/`/`codex-data/`
  to `.gitkeep` placeholders ("runtime-GCS-backed — empty placeholders are fine") and the Dockerfile vendors only
  `_unified-api-contracts/`/`_deployment-service/`/`_strategy-service/`, never a `unified-trading-pm` sibling with
  `plans/active/issues/`. terraform passes no `--pm-repo-path`. So `_resolve_pm_path` returns None, the dedup is never
  invoked, and the full `repository_dispatch` fast-spawn fires on every re-page regardless of the checkpoint. This is
  the structural reason for the 20+ redundant data_pipeline_failure spawns documented in
  dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md — whose final Progress Log entry mis-attributed the
  residual to "checkpoint-write-lag" (a symptom) rather than "the dedup never runs on the monitor host" (the cause).
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [deployment-service, deployment-api]
scope: [engineer, admin]
tags: [monitoring, alerting, escalation, dedup, dp-fetch-009, data-pipeline, orchestrator-capacity, cross-cutting]
related:
  [
    /plans/archive/issues/dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md,
    /plans/active/issues/cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
created: 2026-08-13
author: data_pipeline_failure escalation worker (slot 15, agt-f601e4)
source:
  "DP_RUN_MOSTLY_EMPTY (DP-FETCH-009) STATIC BACKLOG re-fire, asset_group=cefi data_type=book_snapshot_5 — the Nth
  redundant dispatch of an already-resolved condition; the data root cause is fixed and holding, so this worker traced
  why the dispatch keeps firing instead."
assigned_vm: NA
execution_scope: local-only
assigned_role: data_engineering
priority: P2
estimate_class: design
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
drift_direction: advance-code
parent_epic: observability_master
depends_on: []
resolved_by:
locked_by:
last_updated: 2026-08-13
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/archive/issues/dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md,
    deployment-service/deployment_service/data_pipeline_monitors/escalation_dedup.py,
    deployment-service/deployment_service/data_pipeline_monitors/escalation.py,
    deployment-api/cloudbuild.yaml,
  ]
---

# Escalation-dispatch dedup is inert on the monitor host (no PM clone)

## What this is

The dedup mechanism built to stop redundant `data_pipeline_failure` spawns is dead code in production. It reads/writes
its "last verified reading" checkpoint on a **local `unified-trading-pm` clone**, but the host that emits the finding —
the fleet-monitor Cloud Run job on the **deployment-api** image — has no such clone. So the gate can never close, and
every `DP_RUN_MOSTLY_EMPTY` re-page (including correctly-classified STATIC BACKLOG) still full-dispatches a fresh
worker.

This is NOT a data-correctness bug — the underlying `(cefi, book_snapshot_5)` schema-contract regression is fixed and
holding (see `cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md`). It is an observability /
orchestrator-capacity bug: each re-fire wastes a full worker session on an already-resolved condition.

## Measured root cause

1. `escalation.py::route_finding` gates the fast-spawn on `escalation_dedup.check_dispatch_dedup_for_finding(...)`,
   which is only invoked when `_resolve_pm_path(pm_repo_path)` returns a non-None path.
2. `_resolve_pm_path` resolves either a `--pm-repo-path` CLI arg or a `unified-trading-pm` sibling at
   `../unified-trading-pm` / `../../unified-trading-pm` relative to `escalation.py`.
3. The fleet monitor runs on the deployment-api image. `deployment-api/cloudbuild.yaml` empties `pm-plans/` and
   `codex-data/` to `.gitkeep` placeholders ("runtime-GCS-backed — empty placeholders are fine"); the Dockerfile vendors
   `_unified-api-contracts/`, `_deployment-service/`, `_strategy-service/` — never a PM clone with
   `plans/active/issues/`. `data_pipeline_fleet_monitor_scheduler.tf` passes no `--pm-repo-path`.
4. Therefore `_resolve_pm_path` returns None on the monitor host → `check_dispatch_dedup_for_finding` is never called →
   `dedup` is None → the dispatch fires unconditionally.

Convergent confirmation: this worker (slot 15) was itself spawned for a STATIC BACKLOG re-fire; the checkpoint in the
source issue doc's frontmatter (`dp_escalation_checkpoint.max_attempted_at = 2026-08-12T00:00:00Z`) was written by a
POST-dispatch worker (slot 7) running on the AO VM — where a PM clone DOES exist — not by the monitor's own dedup path.

## Why the prior fix didn't hold

`dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md` implemented Option A (dedup on
`max_attempted_at`-since-checkpoint) in `escalation_dedup.py` and shipped it as resolved. The implementation assumed the
monitor can read/write a local PM clone — an assumption that holds on a dev/AO VM but never on the Cloud Run monitor
host. The residual was then recorded (2026-08-12) as "checkpoint-write-lag", which is the symptom, not the cause.

## Recommended decision (operator-gated)

The checkpoint must live somewhere the monitor can read/write durably, and the OPEN-issue index must be reachable from
the monitor host. Options (this is the Option A/B/C call already flagged as pending):

- **A (correct)** — persist the checkpoint to GCS (the monitor already has a storage client) or the orchestrator's
  issue/backlog surface, and resolve the OPEN-issue match from there instead of a local `plans/active/issues/` walk.
- **B (insufficient alone)** — vendor `plans/active/issues/` into the deployment-api image; but the checkpoint write is
  ephemeral (lost on rebuild), so this only works combined with A's durable store.
- **C (alternative)** — move the dedup to the orchestrator side (`/api/escalate` handler /
  `escalate-to-orchestrator.yml`, which runs where the PM clone lives) so it dedups before AutoSpawn.

Marked `assigned_vm: NA` — this is a design decision, not a worker-determinable bounded outcome.

## Todos

- [x] ✅ [DESIGN] P2. Operator/main-agent decision: pick A/B/C (or a variant) for where the dedup checkpoint +
      OPEN-issue index live, so the gate closes on the monitor host. RULED 2026-08-13: **Option A** — persist the
      checkpoint to GCS (the monitor already has a storage client per this doc's own text) and resolve the OPEN-issue
      match from there instead of a local `plans/active/issues/` walk. B is explicitly insufficient alone (ephemeral
      checkpoint, lost on image rebuild) and C (orchestrator-side dedup) adds a cross-service hop for no benefit over A
      when the monitor can already write GCS directly. This matches the filing worker's own recommendation; no new
      information changes that call. Confirmed live 2026-08-13 via `escalation_queue` (`escalation_id=agt-f601e4`,
      `attempts=46`, `reescalations=4`, `resolution=still_red_reescalated`) that the re-fire is still ongoing as of this
      ruling — the CODE todo below is not cosmetic, it is actively burning worker sessions right now.
- [ ] [CODE] P2. Implement the chosen fix (Option A) in `deployment-service` `escalation.py` / `escalation_dedup.py` —
      persist the dispatch-dedup checkpoint to GCS instead of a local PM clone path, so `_resolve_pm_path` returning
      None on the Cloud Run monitor host no longer disables the gate. Then verify by re-firing a STATIC BACKLOG
      `DP_RUN_MOSTLY_EMPTY` and confirming the dispatch is suppressed. Not implemented in this session (design ruling
      only) — deployment-service code change, needs its own scoped session.

## Verification this worker performed (no new data fix needed)

- All five data fixes for the `(cefi, book_snapshot_5)` regression are ancestor-of `origin/live-defi-rollout`:
  `unified-api-contracts@8db188fe` + `@1c4d8864`, `market-tick-data-service@339ca767`, `deployment-service@a564cca`
  (STATIC BACKLOG materiality) + `@1b035c52`/`@9102eb9b` (dispatch dedup).
- The alert fired `is_static_backlog=True` (no new attempted_failed activity in 1d) — correctly classified, no fresh
  data regression.
- GCS was not re-read from this host (the `unified-trading-sa` ADC here lacks access to the prod
  `market-data-tick-cefi-prd` bucket — HTTP 403), so the "zero new schema-contract rows past 2026-07-31" claim rests on
  the source issue doc's own prior live reads + the ancestor checks above, not a fresh query this session.
