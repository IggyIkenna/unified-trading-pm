---
doc_type: plan
title: Deployment registry Firestore migration — Phase 5 — verify at scale + codex SSOT update
summary:
  Prove the migration actually solved the scale ceiling — a synthetic 5,000-doc registry with the inventory query + UI
  render staying under budget, a recorded heartbeat-cadence cost recommendation — then close the loop in the docs by
  updating the deployment-observability codex SSOT with the Firestore-registry contract, the GCS-to-Firestore lineage
  note, and the DynamoDB backend-swap note, plus the CLAUDE.md one-liner.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [deployment-api, unified-trading-pm]
scope: [engineer]
tags: [firestore, deployment-registry, scale-test, codex, verification]
related:
  - deployment_registry_firestore_migration_2026_07_14.md
  - deployment_registry_firestore_p3_cutover_2026_07_14.md
  - deployment_registry_firestore_p4_dynamodb_2026_07_14.md
created: "2026-07-14"
last_updated: "2026-07-14"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: review
drift_direction: advance-code
depends_on:
  - deployment_registry_firestore_p3_cutover_2026_07_14.md
  - deployment_registry_firestore_p4_dynamodb_2026_07_14.md
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: deployment_registry_firestore_migration_2026_07_14.md (master, Phase 5)
---

# Phase 5 — Verify at scale + codex SSOT update

> **Dispatch:** `assigned_role: review` · **model: Sonnet** (default) · **effort: high**. `status: active`;
> `gate_on_depends` holds it until BOTH Phase 3 and Phase 4 are done. Final phase — closes the migration.

## Context (read first — self-contained)

The whole point of the migration was Q1 (scale) + Q2 (partial render). This phase proves Q1 empirically and records the
outcome in the codex SSOT so the next reader understands the registry is now Firestore (GCS-first history preserved only
in docs).

**Gotchas:** the scale test must exercise the REAL query path (`query_by_status` + the census enrichment), not a mock,
to be meaningful. Post-phase codex audit is review-blocking per CLAUDE.md — enumerate the codex paths touched. UTC
datetimes; QG-green.

## Todos

- [ ] [REVIEW] P2. Scale test — seed a synthetic ~5,000-doc `deployments` collection; measure the inventory query +
      census render latency and confirm it stays well under the 45s bound (and that the old download-all path is truly
      gone). Record the numbers + the actual write cost observed vs the estimate in the Progress Log.
- [ ] [REVIEW] P2. Heartbeat-cadence recommendation — from the observed write cost, record the recommended registry
      heartbeat interval at the 100-VM and 5,000-VM points (the cadence lever), noting the resource-sample forensics
      ride the run.log (`utl@600fe4f4`) so slowing the registry write loses no resource history.
- [ ] [REVIEW] P2. Post-phase codex audit — update
      [`codex/05-infrastructure/deployment-observability.md`](../../codex/05-infrastructure/deployment-observability.md): the
      Firestore-registry contract (collection/doc/query), the GCS→Firestore lineage note (GCS-first until 2026-07, then
      Firestore), and the DynamoDB/`cloud_interface` backend-swap note. SUPERSEDED-banner any GCS-registry-specific doc.
- [ ] [REVIEW] P2. Update the CLAUDE.md deployment-observability one-liner (+ any conditional-domain-index pointer) to
      name Firestore as the registry store. Keep within the size budget (condense, don't grow).
- [ ] [INFRA] P2. Ship (commit + push, cite shas), flip this plan's items, and mark the master
      `deployment_registry_firestore_migration_2026_07_14.md` complete — run the archival ritual on the whole
      phase-chain once every phase is done.

## Success criteria

- Inventory query + render stay under the 45s bound at 5,000 synthetic docs (measured, in the Progress Log).
- Heartbeat-cadence recommendation recorded for 100-VM and 5,000-VM scale.
- `deployment-observability` codex updated with the Firestore contract + GCS→Firestore lineage + DynamoDB backend-swap;
  CLAUDE.md one-liner updated within budget.
- QG green.

## Codex SSOTs

- `codex/05-infrastructure/deployment-observability.md` — the SSOT this phase updates.
- `CLAUDE.md` — the deployment-observability one-liner + conditional-domain-index pointer.
