---
doc_type: plan
title: Deployment registry — migrate from GCS-object-per-VM to Firestore (queryable, scalable, AWS-ready) — OVERVIEW
summary:
  Design overview + phase index for migrating the deployment registry (heartbeat + lifecycle state, one JSON blob per VM
  under deployments/active/ in GCS) to Firestore. The GCS-object-per-VM read pattern does not scale — the inventory
  census must download+parse every blob within a 45s bound, so ~3k stale entries already make the prod Deployments tab
  render empty. The migration splits into a draft-gated AO phase-chain — only P0 active, P1-P5 draft, each activated by
  the prior phase (P0 unblock now, P1 dual-write, P2 reader migration + partial-render decouple, P3 cutover + GCS
  decommission, P4 DynamoDB for AWS-readiness, P5 verify at scale + codex). This doc itself is AO-dispatchable
  (reclassified 2026-07-30, na-eligibility-audit) but currently has no open todos of its own — the bulk of dispatched
  work lives in the phase-plans below.
status: active
nature: design
asset_group:
  [ui] # corrected 2026-07-30 (ui-tranche launch) -- was [meta]; deployment registry backs the
  # deployment-ui Deployments tab directly (the "~3k stale entries make the prod Deployments tab render empty" defect)
stage: [meta]
repos: [deployment-api, unified-trading-library, deployment-ui, deployment-service, unified-trading-pm]
scope: [engineer]
tags: [firestore, dynamodb, deployment-registry, observability, migration, scale, cloud-interface]
related:
  - /plans/archive/2026_07/deployment_registry_firestore_p0_unblock_2026_07_14.md
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
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 16
estimate_calibrated_ai_days: 13
assigned_role: infra
drift_direction: advance-code
depends_on:
archive_exempt: true # intentionally NOT archived here — reserved for deployment_registry_firestore_p5_verify_2026_07_14.md's own final todo (see Progress Log 2026-07-30)
locked_by:
locked_since:
supersedes:
superseded_by:
source: interactive session 2026-07-14 (operator + agent diagnosis of empty-inventory prod bug)
context_scope:
  [
    /codex/05-infrastructure/deployment-observability.md,
    /codex/05-infrastructure/gcs-object-operations.md,
    /plans/active/deployment_registry_firestore_p3_cutover_2026_07_14.md,
    /plans/archive/2026_08/issues/deployment_registry_dualwrite_flag_not_propagated_to_vm_launchers_2026_07_30.md,
    deployment-api/deployment_api/routes/deployments_inventory/_registry_io.py,
  ]
---

# Deployment registry → Firestore migration (OVERVIEW + phase index)

> **This is primarily a design/index doc** — `assigned_vm: planning` since the 2026-07-30 na-eligibility-audit
> reclassification (see Progress Log), though it currently has no open todos of its own. The bulk of dispatchable work
> lives in the six phase-plans below (`assigned_vm: planning`), run as a **draft-gated chain**: only **P0 is `active`**
> (dispatches now); **P1–P5 are `draft`** (NOT ingested) and each phase's LAST todo flips the next phase
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
  $13/day,
  DynamoDB ≈ $4.5/day, both cheaper than the current GCS overwrite (~~$36/day). No cross-cloud
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

| Phase  | Plan                                                                                                              | Role             | Model / effort     | Status                                                                                                                                                                                                                                                                                                                                                                             | Gate                                        |
| ------ | ----------------------------------------------------------------------------------------------------------------- | ---------------- | ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| **P0** | [p0 — unblock (reaper + graceful complete)](deployment_registry_firestore_p0_unblock_2026_07_14.md)               | infra            | Sonnet / high      | **active** — reallocated back to AO 2026-07-24 (9 todos then open, 1 `[REVIEW]` P2 todo still open as of 2026-07-25); success criteria (`active/` ≈ running-VM count) not yet fully verified                                                                                                                                                                                       | none — dispatched immediately               |
| **P1** | [p1 — Firestore writer + dual-write](../archive/2026_07/deployment_registry_firestore_p1_dualwrite_2026_07_14.md) | infra            | **Opus** / high    | **complete (archived)**                                                                                                                                                                                                                                                                                                                                                            | activated by P0's last todo · `sequential`  |
| **P2** | [p2 — reader migration + decouple](../archive/2026_07/deployment_registry_firestore_p2_readers_2026_07_14.md)     | backend-engineer | **Opus** / **max** | **complete (archived)**                                                                                                                                                                                                                                                                                                                                                            | activated by P1 (∥ P4) · `sequential`       |
| **P3** | [p3 — cutover + GCS decommission](deployment_registry_firestore_p3_cutover_2026_07_14.md)                         | backend-engineer | **Sonnet** / high  | **active** — self-halted pending an operator GO/NO-GO; blocker has evolved past the original 2026-07-17 empty-Firestore finding — p3_cutover's own 2026-08-08 remeasurement found the collection is NOT empty (2,351 docs, 557 stale `status=running`, only 48/176 live VMs matched — a reaper gap, not an absence of data); see that doc's GO/NO-GO checklist for current numbers | activated by P2 · `sequential` (autonomous) |
| **P4** | [p4 — DynamoDB (AWS-ready)](../archive/2026_07/deployment_registry_firestore_p4_dynamodb_2026_07_14.md)           | infra            | Sonnet / high      | **complete (archived)**                                                                                                                                                                                                                                                                                                                                                            | activated by P1 (∥ P2/P3)                   |
| **P5** | [p5 — verify at scale + codex](deployment_registry_firestore_p5_verify_2026_07_14.md)                             | review           | Sonnet / high      | **draft** — blocked on P3; scope now narrower than originally written (P4's DynamoDB half of the codex-sync mandate is already done via P4's own archival codex-sync)                                                                                                                                                                                                              | activated by P3 or P4 (last to finish)      |

## Todos

- [x] ✅ [DEVOPS] P0. **Retagged from `[OPERATOR]` (2026-07-28 gate-cleanup pass)** — self-service, no operator sign-off
      required: deploy `deployment-api` carrying the dual-write flag (`utl@bf56debe` + `deployment-api@8e93a82`,
      `543860c`), enable `DEPLOYMENT_REGISTRY_FIRESTORE_DUALWRITE=true` (typed config, not `os.getenv`) on the fleet,
      and soak per the operator's 2026-07-14 checklist already on record in
      `deployment_registry_firestore_p3_cutover_2026_07_14.md`'s Progress Log — do not re-ask, re-derive, or re-litigate
      that checklist. **Un-block P3 cutover**: verify all 4 published GO/NO-GO criteria directly — (1) Firestore
      `deployments` doc count ≈ live-VM count with fresh `last_heartbeat_at`; (2) resource stats (cpu/mem/disk/
      heartbeat) render from the Firestore surface in deployment-ui, not the GCS blob; (3) `GET /{id}/detail` returns
      the full per-VM record from Firestore for a sampled set of live VMs; (4) parity — for N sampled live deployments
      the Firestore doc equals the GCS blob (status, `last_heartbeat_at`, counters, resource fields). P3 (GCS
      decommission) is self-halted on this real data-loss guard (prod Firestore `deployments` measured EMPTY
      2026-07-17); the GCS blob delete stays blocked until all 4 criteria measure true, and P5 (verify + codex-sync) —
      **DONE, deploy verified + GO/NO-GO measured FAIL, evidence + finding filed 2026-07-30 (slot 12).** Deploy
      confirmed live: `uts-shared-deployment-api` revision `uts-shared-deployment-api-00332-8gl`, image
      `deployment-api:acdf634`, Cloud Build `b99e78c1-f5fe-449a-ab49-01ffd70f7b31` SUCCESS (commit
      `acdf634187bf7967bd36c983824cb4316a47435d`, descendant of both cited commits), Cloud Run env carries
      `DEPLOYMENT_REGISTRY_FIRESTORE_DUALWRITE=true` — the literal ask is done. GO/NO-GO measured directly against prod:
      criterion 1 FAILS (Firestore `deployments` = 192 docs, all reap-created failed/completed, 0 `status=running`, 0/16
      overlap with live GCE VMs); criteria 2 + 4 untestable as a direct consequence; criterion 3's read-path plumbing
      verified working (`GET /vm-deployments/{id}` correctly serves a Firestore-resident record). Root cause: the Cloud
      Run env flag only governs deployment-api's OWN process (its reads + its own `reap_stale()` sweep, which is what
      produced those 192 docs) — the real write source (`deployment_heartbeat.py`, run ON each VM) reads the flag from
      GCE **instance** metadata, and no real production VM launcher (only a non-prod benchmark launcher) passes it — so
      "on the fleet" was never actually achieved by this deploy alone. Filed as its own scoped finding + fix-todos
      (root-caused, two fix options given, NOT a same-turn fix — 137+ launcher scripts, no single safe choke point):
      `unified-trading-pm@157be4812f4253585cbb96aa365e64fc7d1fad9b`,
      `/plans/archive/2026_08/issues/deployment_registry_dualwrite_flag_not_propagated_to_vm_launchers_2026_07_30.md`.
      **P3's HALT stays correctly in force** — per this todo's own instruction, re-opened to a human/tracked follow-up
      rather than proceeding to any GCS-write-drop/delete step. stays `draft` behind it. **If any of the 4 measured
      criteria fails, re-open to a human** — do not proceed to P3's drop-GCS-write / snapshot-then-delete todos
      regardless.

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
- **na-eligibility-audit 2026-07-30**: RECLASSIFY, conflict-cleared (infra tranche, dispatch agt-30721a) —
  bounded/deterministic-outcome work, no operator gate or live judgment call found; flipped
  `assigned_vm: NA -> planning`. Conflict-check run against all active `assigned_vm: planning` docs in this doc's
  `parent_epic` + the infra tranche's consolidated-closeout digest: zero/milestone-only overlap, clear to proceed.
  Companion gated finalize plan authored: `deployment_registry_firestore_migration_2026_07_14_finalize_2026_07_30.md`.
- **2026-07-30 (slot 12, infra)** — Worked the only open todo. Deploy confirmed already live (`deployment-api:acdf634`,
  build `b99e78c1-f5fe-449a-ab49-01ffd70f7b31` SUCCESS, dual-write flag `true` on Cloud Run env) — the literal deploy
  ask was done before I picked this up. Measured all 4 GO/NO-GO criteria directly against prod (Firestore REST API, full
  pagination + `gcloud compute instances list`): criterion 1 FAILS (0/192 Firestore docs have `status=running`; zero
  overlap with the 16 live GCE VMs) because the Cloud Run flag only reaches deployment-api's own process, not the
  VM-side heartbeat writer (which reads GCE instance metadata that no real launcher sets). Filed
  `/plans/archive/2026_08/issues/deployment_registry_dualwrite_flag_not_propagated_to_vm_launchers_2026_07_30.md` with
  root cause + two fix options + follow-up todos (deliberately NOT fixed inline — touches 137+ VM launcher scripts, no
  safe single choke point, needs its own scoped + soaked change). Todo flipped done with this honest FAIL result; P3's
  HALT is unaffected and stays correctly in force.
- **2026-07-30 (slot 7, infra)** — Worked the gated
  `deployment_registry_firestore_migration_2026_07_14_finalize_2026_07_30.md` twin: independently re-measured GO/NO-GO
  criterion 1 with fresh live data (193 Firestore docs, 0 `status=running`, 0 overlap with 50 currently-live GCE VMs —
  same FAIL, confirmed not stale), added a Progress Log entry to
  `deployment_registry_firestore_p3_cutover_2026_07_14.md` re-confirming its HALT stays in force. **This doc's own
  single todo has been `[x]` since slot-12's pass, but it is intentionally NOT being archived here** — its archival is
  reserved for `deployment_registry_firestore_p5_verify_2026_07_14.md`'s own final todo (own 2026-07-14 Progress Log:
  "the codex/CLAUDE.md doc updates + master archival ... stay BLOCKED on P3 ... completing"), which is still correctly
  blocked. The finalize plan itself archived (its own todo done, no lock); this overview stays `active` until P3
  unblocks and P5 runs.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — the doc's own cited source file
  (`deployment_api/routes/deployments_inventory.py`) is now a package (refactored
  `deployment_api_qg_size_gate_debt_2026_07_30.md`, pure code motion); swapped in the resolving `_registry_io.py` (the
  actual GCS-census read logic this doc's Problem section describes) in place of the archived ci_status precedent link.
