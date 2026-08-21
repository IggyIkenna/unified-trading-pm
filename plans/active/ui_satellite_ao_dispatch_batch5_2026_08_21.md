---
doc_type: plan
title:
  UI satellite AO batch 5 — artifact-pipeline snapshot worker (na-eligibility-audit RECLASSIFY-per-todo-split of
  artifact_pipeline_observability)
summary: >-
  Fifth AO-dispatch batch for the ui tranche, produced by the 2026-08-21 na-eligibility-audit RECLASSIFY-per-todo-split
  pass on `artifact_pipeline_observability_2026_07_17.md`. Extracts the ONE bounded item out of that doc's 4 remaining
  open items (the other 3 stay NA — a design-blocked VM-launch-deploy-provider scoping call, a `_(stretch, optional)_`
  marker, and an already-duplicated-elsewhere doc correction): build the GCS-snapshot worker for `/ops/artifacts`,
  mirroring the existing cost-observability worker's expensive-source → periodic GCS snapshot → cheap local
  DuckDB/TTL-read shape the source plan already names as "the ONE sanctioned shape for an expensive multi-cloud
  source."
status: active
nature: process
asset_group: [ui]
stage: [meta]
repos: [deployment-api]
scope: [engineer]
tags: [ui, ao-dispatch, close-out, batch-5, satellite-docs, artifact-pipeline, snapshot-worker, cost-observability]
related:
  [
    /plans/active/artifact_pipeline_observability_2026_07_17.md,
    /plans/active/ui_satellite_ao_dispatch_batch5_finalize_2026_08_21.md,
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/artifact_pipeline_observability_2026_07_17.md,
    /codex/05-infrastructure/deployment-observability.md,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
    deployment-api/deployment_api/services/artifact_pipeline,
  ]
source: >-
  na-eligibility-audit 2026-08-21 (ui tranche) — RECLASSIFY-per-todo-split of
  `artifact_pipeline_observability_2026_07_17.md`'s Phase 1 "Snapshot worker" todo (P2, downgraded from P1 — the
  live-scan 300s TTL cache covers today's load; this is for long-history + concurrent-load headroom, not urgent).
assigned_role: backend_engineer
effort: low
sequential: false
drift_direction: advance-code
---

# UI satellite AO batch 5 (observability_master) — artifact-pipeline snapshot worker

> **Status: active.** 1 todo, conflict-checked clean against every active `assigned_vm: planning` doc under
> `parent_epic: observability_master` and `deployment_and_user_management_master` (none build a snapshot-worker /
> `artifact-snapshots` path). Low priority (P2, not urgent) — the source plan's live-scan 300s TTL cache already
> covers today's `/ops/artifacts` load; this worker is for long-history + concurrent-load headroom only.

## Todos

- [ ] [BACKEND] P2. **Build the artifact-pipeline snapshot worker** —
      `deployment-api/scripts/artifact_snapshot_worker.py` (or the service's existing scripts/ home; mirror the real
      module path of the shipped cost-observability snapshot worker, don't guess a new location), triggerable via
      Cloud Scheduler or `POST …/snapshot-run` matching the cost-observability worker's own trigger convention.
      Periodically reads the live artifact-pipeline APIs (`services/artifact_pipeline/` — Cloud Build, Artifact
      Registry, Cloud Run revisions, the GCS tarball-manifest provider) and appends normalized parquet to
      `gs://{state}/artifact-snapshots/…` via `resolve_bucket_name(...)` (never an inline `gs://` literal). Read path
      is DuckDB-over-parquet with `deployment_api/utils/bounded_cache.py`'s `BoundedCache(maxsize, ttl)` — never an
      unbounded dict, never a per-request cloud scan (this plan's own "Constraints" section bans that shape). Honour
      the `WORKERS=2` / Cloud Run memory budget already documented in the source plan. Done-when: the worker runs on
      its schedule (or via the manual trigger) and produces a real parquet row set in the target GCS path, a new
      read path serves from the DuckDB/TTL cache (not a live cloud call) when the snapshot is fresh, `deployment-api`
      quality-gates green, and a unit test proves the worker is `--block-network` safe (providers mocked at the same
      seam `test_artifact_pipeline.py` already uses).

## Progress Log

- **2026-08-21**: Extracted from `artifact_pipeline_observability_2026_07_17.md`'s Phase 1 "Snapshot worker" todo by
  na-eligibility-audit (ui tranche, RECLASSIFY per-todo split). Source doc's checkbox flipped `[x]` citing this
  extraction; source doc stays `assigned_vm: NA` for its 3 other open items.
