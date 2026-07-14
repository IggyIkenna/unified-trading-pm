---
doc_type: plan
title: Deployment registry Firestore migration — Phase 3 — cutover to Firestore-only + decommission the GCS registry
summary:
  Once every reader is on Firestore (Phase 2), stop writing GCS — drop the dual-write so Firestore is the sole SSOT —
  then delete the GCS registry blobs after a snapshot, keeping only a codex note of the GCS-to-Firestore lineage. The
  two irreversible steps (drop-GCS-write, delete-blobs) are OPERATOR-gated — an AO worker never flips them autonomously.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-library, deployment-api, unified-trading-pm]
scope: [engineer]
tags: [firestore, deployment-registry, cutover, decommission, migration]
related:
  - deployment_registry_firestore_migration_2026_07_14.md
  - deployment_registry_firestore_p2_readers_2026_07_14.md
created: "2026-07-14"
last_updated: "2026-07-14"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: backend-engineer
model_tier: opus-required
drift_direction: advance-code
depends_on:
  - deployment_registry_firestore_p2_readers_2026_07_14.md
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: deployment_registry_firestore_migration_2026_07_14.md (master, Phase 3)
---

# Phase 3 — Cutover to Firestore-only + decommission the GCS registry

> **Dispatch:** `assigned_role: backend-engineer` · **model: Opus** (`opus-required`) · **effort: high**.
> `status: active`; `gate_on_depends` holds it until Phase 2 is done, `sequential: true` orders its todos. (Phase 4 runs
> in parallel off Phase 1.) **Two OPERATOR-gated irreversible steps** — do not flip them from an AO worker.

## Context (read first — self-contained)

Preconditions: Phase 2 complete — EVERY reader reads Firestore-first (its inventory checklist fully checked), and
dual-write has been populating Firestore correctly. Only now is it safe to stop writing GCS.

Sequence (order matters):

1. Drop the GCS-write half → Firestore-only writes (remove the dual-write flag branch; Firestore is SSOT).
2. Soak Firestore-only for an agreed window; confirm inventory + reaper + detail all correct with zero GCS registry
   writes.
3. Snapshot the GCS registry (export `deployments/active/**` + `deployments/archive/**` to a dated cold prefix) BEFORE
   any delete — irreversible-op insurance.
4. Delete the GCS registry blobs and remove the now-dead GCS registry code paths (no shims — workspace rule: delete
   deprecated code).

**Gotchas:** GCS object deletes go through the UTL wrapper `gcs_delete_object(uri)`
([`cloud_interface/gcs_blob_ops.py:45`](../../unified-trading-library/unified_trading_library/cloud_interface/gcs_blob_ops.py))
— NEVER subprocess `gcloud`/`gsutil` (QG-enforced). The reaper (Phase 0) still runs — after cutover it must reap
Firestore, not GCS (verify it uses the migrated store). Premature step 1 (before all readers migrated) blinds any missed
reader — hence the operator gate. UTC datetimes; QG-green per repo.

## Todos

- [ ] [OPERATOR] P1. GATE — confirm Phase 2's reader inventory is FULLY checked (every reader on Firestore-first) and
      dual-write has been mirroring correctly for the agreed soak. Operator sign-off in the Progress Log before the next
      todo. (Non-dispatchable: `[OPERATOR]`.)
- [ ] [BACKEND] P1. Drop the GCS-write half — remove the dual-write branch so `register`/`heartbeat`/`complete` write
      Firestore ONLY; delete the `deployment_registry_firestore_dualwrite` flag. Firestore is the sole SSOT. Confirm the
      Phase-0 reaper now operates on the Firestore store.
- [ ] [REVIEW] P1. Soak — run Firestore-only for the agreed window; assert inventory, reaper, and `/{id}/detail` are all
      correct with ZERO GCS registry writes (evidence: no new objects under `deployments/active/` + a green inventory).
- [ ] [OPERATOR] P1. GATE — approve GCS registry deletion (IRREVERSIBLE). Operator sign-off in the Progress Log.
      (Non-dispatchable: `[OPERATOR]`.)
- [ ] [BACKEND] P1. Snapshot then delete: first copy `deployments/active/**` + `deployments/archive/**` to a dated
      cold-archive prefix (via `gcs_copy_object`), THEN delete the originals via `gcs_delete_object` (never
      gsutil/subprocess). Remove the dead GCS registry code paths (`ACTIVE_PREFIX`/`ARCHIVE_PREFIX` read/write/list in
      `deployment_registry.py`) — no shims. `bash scripts/quality-gates.sh` green.
- [ ] [INFRA] P3. Ship (commit + push, cite shas) and flip this plan's items (`docs(plans):`). Phase 5 is already
      `active`, held by `gate_on_depends` until this plan and Phase 4 are done — do NOT hand-edit any sibling plan's
      status.

## Success criteria

- Registry writes are Firestore-only; the dual-write flag is gone; the reaper reaps Firestore.
- GCS `deployments/active/**` + `archive/**` are snapshotted then deleted; the GCS registry code is removed (no shims).
- Zero regressions in inventory/reaper/detail during and after the soak.
- GCS deletes via UTL `gcs_delete_object` only; UTC datetimes; QG green.

## Codex SSOTs

- `codex/05-infrastructure/gcs-object-operations.md` — GCS object ops via UTL wrappers (the delete rule).
- `codex/05-infrastructure/deployment-observability.md` — registry SSOT (lineage note added Phase 5).
