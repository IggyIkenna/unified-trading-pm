---
doc_type: plan
title: Deployment registry Firestore migration — Phase 3 — cutover to Firestore-only + decommission the GCS registry
summary:
  Once every reader is on Firestore (Phase 2), stop writing GCS — drop the dual-write so Firestore is the sole SSOT —
  then delete the GCS registry blobs after a snapshot, keeping only a codex note of the GCS-to-Firestore lineage. The
  two irreversible steps (drop-GCS-write, delete-blobs) are made safe by snapshot-before-delete, so the phase runs fully
  autonomously with no human gate.
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
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: backend_engineer
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
> `status: draft` — activated by Phase 2's last todo; `sequential: true` orders its todos. (Phase 4 runs in parallel off
> Phase 1.) **Fully autonomous — NO operator gates.** **Pulled to LOCAL execution 2026-07-14** (`assigned_vm: NA` /
> `execution_scope: local-only`, same as the rest of this phase chain) — see Phase 0's Dispatch note for why. The
> irreversible GCS deletion is made safe by the snapshot-before-delete (recoverable), not a human sign-off; the "all
> readers migrated" check is an agent verification.

> **🔴 BLOCKED (2026-07-14) — DEPLOY + DUAL-WRITE SOAK REQUIRED, DESTRUCTIVE / OPERATOR-GATED.** The verify gate
> (todo 1) ran and HALTED: the prod `deployments` Firestore collection is EMPTY — dual-write has never run on the live
> fleet (the flag defaults off; enabling it needs the deployment-api Cloud Run deploy, which the operator
> deprioritized). P3 drops the GCS-write and DELETES the GCS registry blobs; doing that while Firestore is empty
> destroys the only populated registry (data-loss). This phase CANNOT proceed until: (a) deploy the P1/P2 image, (b)
> enable `deployment_registry_firestore_dualwrite` on the fleet, (c) soak until Firestore mirrors GCS, (d) validate
> parity. Steps a–d are the deploy the operator set aside. Human decision required — see Progress Log.

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
reader — hence the agent reader-migration verification (todo 1) must pass before dropping the GCS write. UTC datetimes;
QG-green per repo.

## Todos

- [x] ✅ [REVIEW] P1. Verify (agent, no human) that every reader in the Phase-2 inventory reads Firestore-first — grep
      the migrated-reader checklist and assert none still parse the GCS `active/` blobs, and that dual-write has been
      mirroring correctly for the agreed soak. If ANY reader is unmigrated, HALT (do not proceed to the GCS-write drop)
      and record the offender in the Progress Log. — **VERIFY RAN → HALT.** The dual-write soak precondition is UNMET:
      the prod `deployments` Firestore collection is EMPTY (0 docs, measured 2026-07-14) because the flag defaults off
      and dual-write has never been enabled on the live fleet (that needs the deployment-api deploy + flag-on, which the
      operator deprioritized). Dropping the GCS-write / deleting GCS blobs now would DESTROY the only populated registry
      while Firestore is empty — a data-loss catastrophe. Correctly HALTING here per this todo's own rule. The remaining
      P3 todos (drop-GCS-write, snapshot+delete) are the irreversible cutover and stay unchecked/BLOCKED until the
      deploy + soak + parity-validation happen. See Progress Log.
- [ ] [BACKEND] P1. Drop the GCS-write half — remove the dual-write branch so `register`/`heartbeat`/`complete` write
      Firestore ONLY; delete the `deployment_registry_firestore_dualwrite` flag. Firestore is the sole SSOT. Confirm the
      Phase-0 reaper now operates on the Firestore store.
- [ ] [REVIEW] P1. Soak — run Firestore-only for the agreed window; assert inventory, reaper, and `/{id}/detail` are all
      correct with ZERO GCS registry writes (evidence: no new objects under `deployments/active/` + a green inventory).
- [ ] [BACKEND] P1. Snapshot then delete (the snapshot IS the recoverability safeguard — no human gate needed): first
      copy `deployments/active/**` + `deployments/archive/**` to a dated cold-archive prefix (via `gcs_copy_object`),
      VERIFY the copy succeeded, THEN delete the originals via `gcs_delete_object` (never gsutil/subprocess). Remove the
      dead GCS registry code paths (`ACTIVE_PREFIX`/`ARCHIVE_PREFIX` read/write/list in `deployment_registry.py`) — no
      shims. `bash scripts/quality-gates.sh` green.
- [ ] [INFRA] P3. Ship (commit + push, cite shas) and flip this plan's items (`docs(plans):`). THEN hand off — activate
      the final phase ONLY IF Phase 4 is already `complete`: set `deployment_registry_firestore_p5_verify_2026_07_14.md`
      frontmatter `status: draft`→`active` and commit. If Phase 4 is not yet done, leave P5 `draft` — Phase 4's last
      todo activates it (whichever of P3/P4 finishes last flips P5).

## Success criteria

- Registry writes are Firestore-only; the dual-write flag is gone; the reaper reaps Firestore.
- GCS `deployments/active/**` + `archive/**` are snapshotted then deleted; the GCS registry code is removed (no shims).
- Zero regressions in inventory/reaper/detail during and after the soak.
- GCS deletes via UTL `gcs_delete_object` only; UTC datetimes; QG green.

## Progress Log

- **2026-07-14 (slot 5, Opus — local execution)** — Ran the todo-1 verify gate → **HALT**.
  - **Reader migration**: the P2 render readers ARE Firestore-first (census + 4 monitors + vm_deployments list +
    vm_admin, via `resolve_active_registry`, deployment-api@8e93a82). Dual-write is wired (P1, utl@bf56debe). So the
    CODE preconditions are met.
  - **Soak precondition UNMET (the blocker)**: prod `deployments` Firestore collection = **0 docs** (measured). The
    `deployment_registry_firestore_dualwrite` flag defaults OFF and has never been enabled on the live fleet, so
    Firestore holds nothing. Enabling it requires the deployment-api Cloud Run deploy of the P1/P2 image + flipping the
    flag + a soak window — the deploy the operator deprioritized ("don't worry about the deployed version").
  - **Why I did NOT proceed**: P3's remaining todos drop the GCS-write (→ Firestore-only) and DELETE
    `deployments/active/**` + `archive/**`. Executing either while Firestore is empty destroys the live registry with no
    populated replacement — an irreversible data-loss event. This is a human-gated destructive op (CLAUDE.md hard-stop:
    "destructive ops beyond local"; data-correctness heartbeat). Correctly halting.
  - **To unblock (operator)**: (a) deploy deployment-api carrying utl@bf56debe + deployment-api@8e93a82; (b) set
    `DEPLOYMENT_REGISTRY_FIRESTORE_DUALWRITE=true` (or the typed config) on the fleet; (c) let dual-write soak until the
    Firestore `deployments` doc count tracks the live fleet; (d) diff a sample (P1 todo6). THEN P3's drop-GCS-write +
    snapshot-then-delete become safe. All code for the cutover is ready; only the prod rollout gates it.

## Codex SSOTs

- `codex/05-infrastructure/gcs-object-operations.md` — GCS object ops via UTL wrappers (the delete rule).
- `codex/05-infrastructure/deployment-observability.md` — registry SSOT (lineage note added Phase 5).
