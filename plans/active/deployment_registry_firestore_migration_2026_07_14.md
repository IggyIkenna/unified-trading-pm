---
doc_type: plan
title: Deployment registry — migrate from GCS-object-per-VM to Firestore (queryable, scalable, AWS-ready) — OVERVIEW
summary:
  Design overview + phase index for migrating the deployment registry (heartbeat + lifecycle state, one JSON blob per VM
  under deployments/active/ in GCS) to Firestore. The GCS-object-per-VM read pattern does not scale — the inventory
  census must download+parse every blob within a 45s bound, so ~3k stale entries already make the prod Deployments tab
  render empty. The migration splits into a draft-gated AO phase-chain — only P0 active, P1-P5 draft, each activated by
  the prior phase (P0 unblock now, P1 dual-write, P2 reader migration + partial-render decouple, P3 cutover + GCS
  decommission, P4 DynamoDB for AWS-readiness, P5 verify at scale + codex). This doc is the non-dispatched index — the
  phase-plans below are the dispatched work.
status: active
nature: design
asset_group: [meta]
stage: [meta]
repos: [deployment-api, unified-trading-library, deployment-ui, deployment-service, unified-trading-pm]
scope: [engineer]
tags: [firestore, dynamodb, deployment-registry, observability, migration, scale, cloud-interface]
related:
  - /plans/active/deployment_registry_firestore_p0_unblock_2026_07_14.md
  - /plans/archive/2026_07/deployment_registry_firestore_p1_dualwrite_2026_07_14.md
  - /plans/archive/2026_07/deployment_registry_firestore_p2_readers_2026_07_14.md
  - /plans/active/deployment_registry_firestore_p3_cutover_2026_07_14.md
  - /plans/archive/2026_07/deployment_registry_firestore_p4_dynamodb_2026_07_14.md
  - /plans/active/deployment_registry_firestore_p5_verify_2026_07_14.md
  - /plans/archive/2026_06/ci_status_firestore_side_store_2026_06_10.md
  - /codex/05-infrastructure/deployment-observability.md
created: "2026-07-14"
last_updated: "2026-07-14"
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 16
estimate_calibrated_ai_days: 13
assigned_role: infra
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source: interactive session 2026-07-14 (operator + agent diagnosis of empty-inventory prod bug)
---

# Deployment registry → Firestore migration (OVERVIEW + phase index)

> **This is the non-dispatched design/index doc** (`assigned_vm: NA`, `execution_scope: local-only`). The dispatchable
> work lives in the six phase-plans below (`assigned_vm: planning`), run as a **draft-gated chain**: only **P0 is
> `active`** (dispatches now); **P1–P5 are `draft`** (NOT ingested) and each phase's LAST todo flips the next phase
> `draft`→`active` once its work completes — so no downstream phase can be worked out of order (`gate_on_depends` alone
> proved leaky). Fully autonomous — no operator gates; the irreversible GCS deletion is made safe by
> snapshot-before-delete (recoverable), so no human sits in the loop.

## Problem

The deployment registry stores one small JSON blob per deployment at
`gs://deployment-scripts-<project>/deployments/active/<deployment_id>.json`, overwritten every ~60s by the VM's
heartbeat
([UTL `deployment_registry.py`](../../unified-trading-library/unified_trading_library/deployment_registry.py)), moved to
`deployments/archive/<YYYY-MM-DD>/` on graceful `complete()`. Three structural failures:

1. **The read pattern is O(N-entries), not O(live-VMs).** The inventory census
   ([`deployments_inventory.py`](../../deployment-api/deployment_api/routes/deployments_inventory.py)) downloads +
   parses every `active/` blob (+ a 7-day `archive/` window) on each refresh (~14.7 ms/entry → ~48s for `active/` alone,
   ~138s with archive), inside a hard **45s bound** (`_PROVIDER_CENSUS_TIMEOUT_SEC`); on timeout it discards the ENTIRE
   census including the live VMs. **Measured 2026-07-14: 3,270 active entries (3,060 distinct VMs) for 44 real VMs →
   census times out → prod Deployments tab renders empty for everyone** (reproduced against the deployed in-region API).

2. **Ghost accumulation.** `active/<id>.json` is deleted only by `complete()` (graceful exit). Backfill/market-data VMs
   default to SPOT (workspace HARD RULE) and are preempted/OOM-killed without calling `complete()` → orphaned at
   `status=running` with a frozen heartbeat (3,240 of 3,270 have heartbeats ≥1 day stale). The `reap_stale` reaper
   exists and is correct but is only reachable via a manual `POST /vm-deployments/reconcile` — nothing schedules it.

3. **Won't scale + no partial render.** Even a perfectly-reaped `active/` of 5,000 LIVE entries blows the 45s budget
   (hygiene ≠ scalability). And because "which VMs exist" (fast, GCE) is welded to "registry enrichment" (slow, N
   downloads) in one bounded call, a slow registry read nukes the whole VM list instead of degrading a column.

## Approved design (operator, 2026-07-14)

- **Firestore** doc-per-deployment (`deployments/{deployment_id}`), behind a cloud-agnostic `DeploymentRegistryStore`
  interface in **UTL's `cloud_interface`** (same home as `resolve_bucket_name`). Reads become one indexed query
  (`where status == running`) or a real-time listener, not N downloads. Reuses `firestore_lifecycle.py` (client) +
  `ci_status_store.py` (CAS/`is_stale_write` ordering). → solves #1, #3.
- **Decouple existence from enrichment** — census renders rows from the fast GCE list; registry metadata is best-effort
  per row (slow/absent registry → "—" columns, never a missing row). → solves #3 partial-render.
- **AWS-ready** — a **DynamoDB** backend behind the same interface, cloud-selected (GCP → Firestore, AWS → DynamoDB)
  like `resolve_bucket_name` selects GCS vs S3. Both are ~~free at 10–100 VMs; at 5,000 VMs Firestore ≈
  $13/day, DynamoDB
  ≈ $4.5/day, both cheaper than the current GCS overwrite (~~$36/day). No cross-cloud
  Firestore-from-AWS.
- **Heartbeat cadence is the cost lever** — cost scales linearly with write frequency; dial to 2–5 min at high scale
  (resource-sample forensics ride the run.log per `utl@600fe4f4`, so a slower registry write loses no resource history).
- **Safe migration, never a flag-day** — dual-write → migrate every reader (dual-write outlives the last reader) →
  cutover → decommission, mirroring the completed `ci_status_firestore_side_store_2026_06_10.md`.
- **History in docs, not data** — after decommission the GCS blobs are deleted; a codex note records the GCS→Firestore
  lineage.

## Phase index (the dispatched work)

> **[⚠️ REFRESHED 2026-07-21, plan-reconcile]** — this table + the `related:` links above were stuck at the 2026-07-14
> initial-draft snapshot; the chain has actually progressed to P3. Corrected below (was: P1/P2/P4 all shown `draft`,
> `related:` links pointing at `plans/active/...` with no `../archive/` prefix).

| Phase  | Plan                                                                                                              | Role             | Model / effort     | Status                                                                                                                                                                | Gate                                        |
| ------ | ----------------------------------------------------------------------------------------------------------------- | ---------------- | ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| **P0** | [p0 — unblock (reaper + graceful complete)](deployment_registry_firestore_p0_unblock_2026_07_14.md)               | infra            | Sonnet / high      | **complete**                                                                                                                                                          | none — dispatched immediately               |
| **P1** | [p1 — Firestore writer + dual-write](../archive/2026_07/deployment_registry_firestore_p1_dualwrite_2026_07_14.md) | infra            | **Opus** / high    | **complete (archived)**                                                                                                                                               | activated by P0's last todo · `sequential`  |
| **P2** | [p2 — reader migration + decouple](../archive/2026_07/deployment_registry_firestore_p2_readers_2026_07_14.md)     | backend-engineer | **Opus** / **max** | **complete (archived)**                                                                                                                                               | activated by P1 (∥ P4) · `sequential`       |
| **P3** | [p3 — cutover + GCS decommission](deployment_registry_firestore_p3_cutover_2026_07_14.md)                         | backend-engineer | **Opus** / high    | **active** — self-halted on a real data-loss guard (prod Firestore `deployments` measured EMPTY 2026-07-17; GCS delete blocked pending an operator GO/NO-GO)          | activated by P2 · `sequential` (autonomous) |
| **P4** | [p4 — DynamoDB (AWS-ready)](../archive/2026_07/deployment_registry_firestore_p4_dynamodb_2026_07_14.md)           | infra            | Sonnet / high      | **complete (archived)**                                                                                                                                               | activated by P1 (∥ P2/P3)                   |
| **P5** | [p5 — verify at scale + codex](deployment_registry_firestore_p5_verify_2026_07_14.md)                             | review           | Sonnet / high      | **draft** — blocked on P3; scope now narrower than originally written (P4's DynamoDB half of the codex-sync mandate is already done via P4's own archival codex-sync) | activated by P3 or P4 (last to finish)      |

## Migration invariants (hold across every phase)

- Never a flag-day — dual-write outlives the last reader; every reader cutover is Firestore-first with a LOUD GCS
  fallback.
- Irreversible steps (drop-GCS-write, delete-blobs) are made recoverable by snapshot-before-delete — no human gate; the
  pipeline is fully autonomous.
- Firestore/DynamoDB SDKs are lazy-imported (QG bans top-level `google.cloud`/`boto3` + `try/except ImportError`); flags
  are typed `UnifiedCloudConfig` fields (no `os.getenv`); GCS deletes via UTL `gcs_delete_object` (no gsutil); UTC
  datetimes; `quality-gates.sh`-green before every commit.

## Success criteria (overall)

- prod Deployments tab renders the live fleet within the 45s bound at every scale from 10 to 5,000 VMs.
- A registry-read failure degrades enrichment columns, never the row set (proven by fault injection).
- Registry reads are one indexed query, not N downloads; GCS `active/` blobs are gone; a codex note records the
  GCS→Firestore lineage.
- The same `DeploymentRegistryStore` contract passes on Firestore and DynamoDB; cloud selection is automatic.

## Codex SSOTs

- `/codex/05-infrastructure/deployment-observability.md` — registry-classification SSOT (updated in P5).
- `/codex/05-infrastructure/gcs-object-operations.md` — GCS delete via UTL wrappers (P3).
- Precedent: archived `ci_status_firestore_side_store_2026_06_10.md` (the proven GCS→Firestore phasing).

## Out of scope (named successors)

- Real-time UI listeners (push instead of poll) — a follow-up once Firestore reads land.
- Archiving the emitted `lifecycle-events` / resource samples to a durable event log — separate finding, own plan.
- The run.log whole-file-overwrite efficiency (GCS `compose`/rotation) — separate; soft-delete confirmed OFF so no cost
  leak, VM-side waste only.

## Progress Log

- 2026-07-14 — Overview + 6-phase chain authored (interactive session). Diagnosis: 3,270 active entries / 44 live VMs →
  census timeout → empty prod inventory. Firestore-behind-cloud_interface + DynamoDB-for-AWS approved by operator; model
  split Opus(P1–P3)/Sonnet(P0,P4,P5), effort high floor (P2 max). `utl@600fe4f4` already shipped the `RESOURCE_SAMPLE`
  run.log forensic marker (separate, related). 2026-07-14 — all 6 phase-plans set `status: active` and machine-ordered
  via `gate_on_depends` (+ `sequential: true` on P1–P3) per operator instruction; P0 dispatches immediately, the rest
  are held until their prerequisites finish.
- 2026-07-14 (correction) — `gate_on_depends` proved LEAKY: AO worker slot-11 worked a P4 task out of order (DynamoDB
  provisioning before P1 exists, `eb2a87e56`). Switched P1–P5 to `status: draft` (ironclad not-ingested) + a draft-gated
  handoff (each phase's last todo activates the next); removed P3's `[OPERATOR]` gates (snapshot-before-delete is the
  safeguard, no human in the loop). Only P0 is dispatchable now (`4efa7502c` + this follow-up).
