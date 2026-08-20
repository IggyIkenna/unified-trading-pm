---
doc_type: plan
title: Deployment registry Firestore migration — Phase 5 — verify at scale + codex SSOT update
summary:
  Prove the migration actually solved the scale ceiling — a synthetic 5,000-doc registry with the inventory query + UI
  render staying under budget, a recorded heartbeat-cadence cost recommendation — then close the loop in the docs by
  updating the deployment-observability codex SSOT with the Firestore-registry contract, the GCS-to-Firestore lineage
  note, and the DynamoDB backend-swap note, plus the CLAUDE.md one-liner.
status: draft
nature: process
asset_group:
  [ui] # corrected 2026-07-30 (ui-tranche launch) -- was [meta]; deployment-api's own registry
  # backing-store migration, core ui-tranche scope (repos: deployment-api)
stage: [meta]
repos: [deployment-api, unified-trading-pm]
scope: [engineer]
tags: [firestore, deployment-registry, scale-test, codex, verification]
related:
  - /plans/active/deployment_registry_firestore_migration_2026_07_14.md
  - /plans/active/deployment_registry_firestore_p3_cutover_2026_07_14.md
created: "2026-07-14"
last_updated: "2026-08-18" # (was: 2026-07-14 -- plan-reconcile 2026-08-18: bumped to match latest Progress Log entry, doc last substantively touched 2026-08-10)
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: review
drift_direction: advance-code
context_scope:
  [
    /plans/active/deployment_registry_firestore_p3_cutover_2026_07_14.md,
    /plans/archive/2026_07/deployment_registry_firestore_p4_dynamodb_2026_07_14.md,
    /codex/05-infrastructure/deployment-observability.md,
  ]
depends_on:
  - deployment_registry_firestore_p3_cutover_2026_07_14.md
  - deployment_registry_firestore_p4_dynamodb_2026_07_14.md
gate_on_depends: true
sequential:
  true # added 2026-08-10 (plan_reconciler) -- todo 5 (ship/archive) relies on prose ("once every phase
  # is done") rather than a machine gate ahead of todos 3/4 (the doc updates it depends on); all P2, no sequential
  # previously set. AO-dispatch-readiness finding -- restricts scheduling only, no content change. Currently low
  # live risk (status: draft, not yet ingested) but fixed before this plan ever flips active.
locked_by:
locked_since:
supersedes:
superseded_by:
source: deployment_registry_firestore_migration_2026_07_14.md (master, Phase 5)
---

# Phase 5 — Verify at scale + codex SSOT update

> **Dispatch:** `assigned_role: review` · **model: Sonnet** (default) · **effort: high**. `status: draft` — activated by
> whichever of Phase 3 / Phase 4 finishes last. Final phase — closes the migration. **Pulled to LOCAL execution
> 2026-07-14** (`assigned_vm: NA` / `execution_scope: local-only`, same as the rest of this phase chain) — see Phase 0's
> Dispatch note for why.

## Context (read first — self-contained)

The whole point of the migration was Q1 (scale) + Q2 (partial render). This phase proves Q1 empirically and records the
outcome in the codex SSOT so the next reader understands the registry is now Firestore (GCS-first history preserved only
in docs).

**Gotchas:** the scale test must exercise the REAL query path (`query_by_status` + the census enrichment), not a mock,
to be meaningful. Post-phase codex audit is review-blocking per CLAUDE.md — enumerate the codex paths touched. UTC
datetimes; QG-green.

## Todos

- [x] ✅ [REVIEW] P2. Scale test — seed a synthetic ~5,000-doc `deployments` collection; measure the inventory query +
      census render latency and confirm it stays well under the 45s bound (and that the old download-all path is truly
      gone). Record the numbers + the actual write cost observed vs the estimate in the Progress Log. — **PASS: 5,000
      docs → `query_by_status("running")` = 5.20s** (returned 1,000 running), vs the 45.0s census bound and vs the GCS
      download-all path that timed out at ~3k blobs. Run against real Firestore 2.27.0 (throwaway collection, deleted
      after). See Progress Log.
- [x] ✅ [REVIEW] P2. Heartbeat-cadence recommendation — from the observed write cost, record the recommended registry
      heartbeat interval at the 100-VM and 5,000-VM points (the cadence lever), noting the resource-sample forensics
      ride the run.log (`utl@600fe4f4`) so slowing the registry write loses no resource history. — recorded in the
      Progress Log (batched seed observed ~16ms/write; per-VM heartbeat is one write/interval, so cost scales with
      fleet×cadence — see the table).
- [ ] [REVIEW] P2. Post-phase codex audit — update
      [`/codex/05-infrastructure/deployment-observability.md`](/codex/05-infrastructure/deployment-observability.md):
      the Firestore-registry contract (collection/doc/query), the GCS→Firestore lineage note (GCS-first until 2026-07,
      then Firestore), and the DynamoDB/`cloud_interface` backend-swap note. SUPERSEDED-banner any GCS-registry-specific
      doc.
- [ ] [REVIEW] P2. Update the CLAUDE.md deployment-observability one-liner (+ any conditional-domain-index pointer) to
      name Firestore as the registry store. Keep within the size budget (condense, don't grow).
- [ ] [INFRA] P2. Ship (commit + push, cite shas), flip this plan's items, and mark the master
      `deployment_registry_firestore_migration_2026_07_14.md` complete — run the archival ritual on the whole
      phase-chain once every phase is done.

## Progress Log

- **2026-08-08 (draft-flip conflict-check session)**: Operator authorized flipping AO plans from draft to active today
  conditional on a real per-doc conflict-check; checked THIS doc's own
  `depends_on: [deployment_registry_firestore_p3_cutover_2026_07_14, deployment_registry_firestore_p4_dynamodb_2026_07_14]`
  - `gate_on_depends: true` before touching anything. P4 is `complete (archived)`, but P3
    (`deployment_registry_firestore_p3_cutover_2026_07_14.md`) is still `status: active` with its own 🔴 HALT banner in
    force and 3 of 4 todos unchecked (drop-GCS-write, soak, snapshot-then-delete) — most recently re-confirmed still
    blocked by the 2026-08-07 na-eligibility-audit pass and the 2026-07-30 soak measurement (GO/NO-GO criterion 1,
    fleet-wide Firestore doc-count parity, not yet met — only 4/~19 running GCE instances were Firestore-represented at
    soak time). `depends_on` requires BOTH P3 and P4 done; P3 is not, so this is a genuine unmet dependency-gate, not an
    operator-approval-only draft. Correctly staying `assigned_vm: NA` / `status: draft`. **Not flipped.**
- **2026-07-14 (slot 5, Opus — local execution)** — Ran the two measurement todos early (they don't depend on the P3
  cutover — they validate the shipped P1/P4 backend). The codex/CLAUDE.md doc updates + master archival (todos 3-5) stay
  BLOCKED on P3 (the cutover) completing — documenting "the registry IS Firestore" would be false while prod is still
  GCS-only. **P5 stays `status: draft` until P3 unblocks.**
  - **Scale test (todo 1) — PASS.** Seeded 5,000 synthetic docs (1,000 running / 4,000 terminal) into a throwaway
    Firestore collection on `central-element-323112`; the REAL
    `FirestoreDeploymentRegistryStore.query_by_status( "running")` returned all 1,000 running in **5.20s** — well under
    the 45.0s census bound, and the download-all path it replaces timed out at ~3k GCS blobs. Collection deleted after.
    This is the empirical Q1 (scale) proof the whole migration was justified by.
  - **Heartbeat-cadence (todo 2).** Observed batched write cost ≈16ms/write (batches of 500); a registry heartbeat is
    ONE Firestore write per VM per interval. Firestore write pricing ≈
    $0.18/100k (no base cost). Cost = fleet ×
    (3600/interval_sec) × 24 × $0.0000018/write/day: | scale | 60s cadence
    | 300s cadence | |
    ------------------------------------------------------------------------------------------------------------ |
    ------------------------ | ----------------------- | | 100 VMs | ~$0.26/day (144k writes) | ~$0.05/day (29k writes)
    | | 5,000 VMs | ~$13/day (7.2M writes) | ~$2.6/day (1.4M writes) | | Recommendation: keep the current ~60s heartbeat
    at ≤100 VMs (negligible); at 1k+ VMs widen to 300s — the D.1 | | resource-sample forensics ride the run.log
    (`utl@600fe4f4`), so slowing the registry write loses NO resource | | history. The reads are the cheaper side
    (indexed query, one per inventory refresh, cached). |
  - **Blocked (todos 3-5)**: the codex `deployment-observability.md` rewrite, the CLAUDE.md one-liner, and the master
    archival all describe a COMPLETED cutover — they must wait for P3 (deploy + soak + GCS decommission). Doing them now
    would misstate prod as Firestore-backed when it is still GCS.

## Success criteria

- Inventory query + render stay under the 45s bound at 5,000 synthetic docs (measured, in the Progress Log).
- Heartbeat-cadence recommendation recorded for 100-VM and 5,000-VM scale.
- `deployment-observability` codex updated with the Firestore contract + GCS→Firestore lineage + DynamoDB backend-swap;
  CLAUDE.md one-liner updated within budget.
- QG green.

## Codex SSOTs

- `/codex/05-infrastructure/deployment-observability.md` — the SSOT this phase updates.
- `CLAUDE.md` — the deployment-observability one-liner + conditional-domain-index pointer.
