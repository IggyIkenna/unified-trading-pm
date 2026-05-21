---
title: "GAP-2.4.D — Deployment-API Reader Repoint: flat → env-tiered bucket names"
created: 2026-05-22
author: slot-4
parent_epic: deployment_and_user_management_master
assigned_vm: planning-vm-1
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
locked_by: live-defi-rollout
locked_since: 2026-05-22
---

> **TIMING CONSTRAINT — HARD**: deployment-api reads buckets continuously. Its bucket-name source MUST flip in lockstep
> with the flat→env-tiered data migration (Phase 0d in `code_freeze_migrate_backfill_sequencing_2026_05_10.md`).
> Premature repoint → data-status UI breaks for all asset_groups. This plan ships the CODE half; execution is gated on
> Phase 0d cutover.

## Context

`bucket_name_ssot_canonicalisation_2026_05_10.md` requires that every GCS consumer call
`resolve_bucket_name(cloud, kind, asset_group)` instead of constructing f-string bucket names. QG STEP 5.69 enforces
this in service code. Deployment-api is a special case: it is a read-only consumer of every service's GCS output, and it
runs continuously in Cloud Run — so its bucket resolution must flip atomically with the data migration.

This document is the "done-def #6 extension" referenced in GAP-2.4.D:

> update reader/writer audit table verifying every consumer post-Phase-0d hits env-tiered bucket names (not flat)

---

## Current State Audit (2026-05-22)

### Already migrated — already call `resolve_bucket_name()` ✅

| File                                | Location                                             | How resolved                                                                                     |
| ----------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `services/data_status_drilldown.py` | `build_bucket_name(service, asset_group)` (line 101) | Delegates via `_SERVICE_TO_KIND` → `resolve_bucket_name(cloud="gcp", kind=..., asset_group=...)` |
| `services/upcoming_fixtures.py`     | `_get_sports_bucket()` (line 58)                     | `resolve_bucket_name(cloud="gcp", kind="instruments-store", asset_group="sports")`               |
| `routes/batch_config_utils.py`      | All bucket mappings (lines 29–71)                    | `resolve_bucket_name(...)` throughout                                                            |
| `services/data_query_service.py`    | Sports availability index (line 466)                 | `resolve_bucket_name(cloud="gcp", kind="instruments-store", asset_group="sports")`               |
| `services/data_status_drilldown.py` | Sports fixture readers (lines 1731, 1800)            | `resolve_bucket_name(cloud="gcp", kind="instruments-store", asset_group="sports")`               |

### Still flat — flat f-string template ❌ (must migrate in Phase 0d window)

| File                                   | Class               | Method                                   | Current implementation                                |
| -------------------------------------- | ------------------- | ---------------------------------------- | ----------------------------------------------------- |
| `services/data_status_service.py:2538` | `DataStatusService` | `build_bucket_name(prefix, category)`    | `f"{prefix}-{category.lower()}-{self.project_id}"`    |
| `services/data_query_service.py:41`    | `DataQueryService`  | `build_bucket_name(prefix, asset_group)` | `f"{prefix}-{asset_group.lower()}-{self.project_id}"` |

**Callsites using the still-flat methods:**

`DataStatusService.build_bucket_name`:

- `data_status_service.py:6038` — inside `_get_bucket_name_for_service()`

`DataQueryService.build_bucket_name`:

- `data_query_service.py:175` — `build_bucket_name(mapping.get("prefix"), ag)`
- `data_query_service.py:231` — `build_bucket_name("instruments", asset_group)`
- `data_query_service.py:743` — `build_bucket_name("market-data", asset_group.lower())`

### ml-\* drift check — RESOLVED ✅

Both `data_status_drilldown._SERVICE_TO_KIND` and `data_status_service._SERVICE_TO_KIND` already have:

```python
"ml-service": "ml-models-store"
```

`deployment-service/configs/cloud-providers.yaml` defines both kinds:

- `ml-models-store` (final model artefacts)
- `ml-predictions-store` (variant metrics)

Neither service maps "ml-service" to a flat `f"ml-*-{pid}"` template. The L5.1↔L5.2 drift noted in the `code_freeze`
plan (yaml SSOT wins: `ml-models-store` / `ml-predictions-store`) is already resolved — no further action needed.

---

## Migration Approach

### Option A — Delete flat methods; replace callsites with `data_status_drilldown.build_bucket_name` (recommended)

`data_status_drilldown.build_bucket_name` already does the right thing (`_SERVICE_TO_KIND` → `resolve_bucket_name`). The
two flat methods in `DataStatusService` and `DataQueryService` duplicate its logic incorrectly (flat template vs
env-tiered). The fix:

1. Delete `DataStatusService.build_bucket_name` and `DataQueryService.build_bucket_name`.
2. In each callsite, replace with either:
   - `data_status_drilldown.build_bucket_name(service_name, asset_group)` if the call has a service-name context, OR
   - direct `resolve_bucket_name(cloud="gcp", kind=kind_str, asset_group=ag)` if the mapping is trivial.
3. Run `basedpyright deployment_api/` + `bash scripts/quality-gates.sh` to verify.

**Why preferred**: eliminates the duplicate `_SERVICE_TO_KIND` dict in `data_status_service.py` (lines 2768–2790) and
ensures a single resolution path.

### Option B — Add `_SERVICE_TO_KIND` delegation inside the flat methods

Leave `build_bucket_name` methods in place but rewrite their bodies to call `resolve_bucket_name`. This retains the
internal API surface (useful if other tests mock these methods directly).

**Why not preferred**: keeps duplication; existing tests mock `build_bucket_name` inline which masks resolution bugs.

---

## Execution Plan

- [ ] [SCRIPT] P0. **Code half** (ships pre-Phase-0d; gates on Phase-0d execution):
  - Delete `DataStatusService.build_bucket_name` at `data_status_service.py:2538`.
  - Delete `DataQueryService.build_bucket_name` at `data_query_service.py:41`.
  - Fix 4 callsites: `data_status_service.py:6038`, `data_query_service.py:175/231/743` — replace with
    `data_status_drilldown.build_bucket_name(service, asset_group)` or direct `resolve_bucket_name(...)`.
  - Remove the duplicate `_SERVICE_TO_KIND` dict from `data_status_service.py` (lines 2768–2790) — canonical copy lives
    in `data_status_drilldown.py`.
  - `basedpyright deployment_api/` → 0 errors. `bash scripts/quality-gates.sh` → exit 0.
  - Push to deployment-api tab branch (NOT LDR until Phase-0d cutover window opens).

- [ ] [TEST] P0. Update/add unit tests:
  - `tests/unit/test_data_status_service.py` — remove any tests that mock `DataStatusService.build_bucket_name`
    directly; replace with `resolve_bucket_name` mock at UTL boundary.
  - `tests/unit/test_data_query_service.py` — same.

- [ ] [DOC] P1. **Flip GAP-2.4.D checkbox** in `code_freeze_migrate_backfill_sequencing_2026_05_10.md` once code half is
      pushed. Execution half (Phase 0d cutover + data-status UI smoke test post-repoint) remains `[ ]` until the
      migration window.

---

## Timing Constraint

```
Phase 0c  — operator provisions env-tiered prod buckets (GCP + AWS)
Phase 0d  — migrate flat-bucket data into env-tiered buckets (pause writes)
              → THIS is the cutover window for deployment-api repoint
              → merge deployment-api tab branch → LDR in this window
              → smoke the data-status UI post-merge to verify drill-down still works
```

Pre-repoint (before Phase 0d window): deployment-api reads flat bucket names → data in flat buckets → UI works.
Post-repoint + post-migration: deployment-api reads env-tiered names → data in env-tiered buckets → UI works.
Post-repoint but pre-migration: deployment-api reads env-tiered names → data still in flat buckets → UI broken.

**Do NOT merge to LDR before Phase 0d migration window opens.**

---

## Temporary states + their canonical follow-up plans

| State                                              | Successor                                                                                      |
| -------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Code half on tab branch, not merged                | Merge in Phase 0d window per `code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 2.1 |
| `[ ]` GAP-2.4.D execution half in code_freeze plan | Remains open until Phase 0d cutover + data-status UI smoke                                     |
