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
asset_group:
  [ui] # corrected 2026-07-30 (ui-tranche launch) -- was [meta]; deployment-api's own registry
  # backing-store migration, core ui-tranche scope
stage: [meta]
repos: [unified-trading-library, deployment-api, unified-trading-pm]
scope: [engineer]
tags: [firestore, deployment-registry, cutover, decommission, migration]
related:
  - /plans/active/deployment_registry_firestore_migration_2026_07_14.md
  - /plans/archive/2026_07/deployment_registry_firestore_p2_readers_2026_07_14.md
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
model_tier:
  sonnet # corrected 2026-08-10 (plan_reconciler) -- opus-required has NO standing category left per
  # CLAUDE.md's 2026-08-07/08-08 ruling ("opus-required = ZERO categories -- opus is now manual-only"); was stale
  # since 2026-07-14 creation
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
context_scope:
  [
    /codex/05-infrastructure/gcs-object-operations.md,
    /codex/05-infrastructure/deployment-observability.md,
    /plans/active/deployment_registry_firestore_migration_2026_07_14.md,
    /plans/archive/2026_08/issues/deployment_registry_dualwrite_flag_not_propagated_to_vm_launchers_2026_07_30.md,
    unified-trading-library/unified_trading_library/cloud_interface/gcs_blob_ops.py,
  ]
---

# Phase 3 — Cutover to Firestore-only + decommission the GCS registry

> **Dispatch:** `assigned_role: backend-engineer` · **model: Opus** (`opus-required`) · **effort: high**.
> `status: active` (activated by Phase 2's last todo, per frontmatter — this line corrected 2026-07-21, plan-reconcile:
> was stale `draft` boilerplate copied from the phase-chain template and never updated on activation);
> `sequential: true` orders its todos. (Phase 4 runs in parallel off Phase 1.) **Fully autonomous — NO operator gates.**
> **Pulled to LOCAL execution 2026-07-14** (`assigned_vm: NA` / `execution_scope: local-only`, same as the rest of this
> phase chain) — see Phase 0's Dispatch note for why. The irreversible GCS deletion is made safe by the
> snapshot-before-delete (recoverable), not a human sign-off; the "all readers migrated" check is an agent verification.

> **🔴 BLOCKED (2026-07-14) — GCS DELETE HELD UNTIL OPERATOR CONFIRMS THE FLEET IS ON FIRESTORE (operator decision
> 2026-07-14).** The verify gate (todo 1) ran and HALTED: the prod `deployments` Firestore collection is EMPTY —
> dual-write has never run on the live fleet (the flag defaults off; enabling it needs the deployment-api deploy). The
> operator's explicit ruling: **the GCS delete (todo 4) stays BLOCKED until we can SEE the fleet using the new path —
> specifically until (i) VMs are writing to Firestore, (ii) VM resource stats (cpu/mem/disk/heartbeat) are READ from the
> Firestore surface in the deployment-ui, and (iii) per-VM data (the `/{id}/detail` drill-down) is retrievable from
> Firestore.** Only after that is confirmed does the snapshot→delete run. Concrete unblock sequence + the GO/NO-GO
> verification are in the Progress Log. Nothing destructive happens before that confirmation.

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

- **2026-07-14 (operator decision)** — The GCS delete (todo 4) is held explicitly until we can SEE the fleet on the new
  path. **DELETE GO/NO-GO checklist** (all must be true before the snapshot→delete runs):
  1. **Fleet writing Firestore** — the `deployments` collection is non-empty AND its doc count ≈ the live-VM count, with
     `last_heartbeat_at` values fresh (VMs are actively writing through the new path, not a stale one-time backfill).
  2. **Resource stats read from the new surface** — the deployment-ui Deployments tab shows each VM's cpu/mem/disk/
     heartbeat sourced from the Firestore doc (the D.1 host-metric fields), not the GCS blob. (P2 already routes the
     LIST view's resource columns through `resolve_active_registry`; this phase adds the `/{id}/detail` drill-down — see
     the 2026-07-14 detail-read routing note below.)
  3. **Per-VM data retrievable from Firestore** — `GET /{id}/detail` returns the full per-VM record from Firestore for a
     sampled set of live VMs (the drill-down popover renders with real data).
  4. **Parity** — for N sampled live deployments the Firestore doc equals the GCS blob (status, last_heartbeat_at,
     counters, resource fields). Only when 1–4 hold does the snapshot→delete run (and even then: snapshot to a dated
     cold prefix FIRST, verify the copy, then delete). Until then the GCS registry stays authoritative and untouched.

- **2026-07-14 (slot 5, Opus) — detail-read routing shipped toward the gate (deployment-api@543860c).** To make GO/NO-GO
  items 2–3 achievable, the per-VM point reads now route Firestore-first via a new `resolve_deployment_by_id()` (GCS
  fallback), companion to P2's `resolve_active_registry()`: the `vm_deployments GET /{id}` + the experiment-action
  pre-read. The `/{name}/detail` drill-down + its resource-stat columns (cpu/mem/disk/host-metrics) ALREADY read
  Firestore via the census cache P2 routed. So once dual-write is on, per-VM data + resource stats come from Firestore.
  Additive + safe (fallback preserved); it does NOT drop the GCS write or delete anything — those stay blocked per the
  checklist above.

- **2026-07-30 (slot 7, infra) — re-checked the DELETE GO/NO-GO checklist's precondition; HALT stays correctly in
  force.** Dispatched via `deployment_registry_firestore_migration_2026_07_14_finalize_2026_07_30.md` (gated finalize
  plan, itself gated on the sibling migration-overview doc's dual-write-deploy todo, which slot-12 flipped `[x]` earlier
  today with an honest FAIL result — see that doc's Progress Log and
  `/plans/archive/2026_08/issues/deployment_registry_dualwrite_flag_not_propagated_to_vm_launchers_2026_07_30.md`).
  Independently re-measured criterion 1 with fresh live data (did not just trust slot-12's snapshot): Firestore REST
  API, full pagination, prod `deployments` collection = **193 docs** (190 `status=failed`, 3 `status=completed`, **0
  `status=running`**); cross-referenced every doc's `vm_name` against **50** currently-`RUNNING` GCE instances
  (`gcloud compute instances list --filter=status=RUNNING`, project `central-element-323112`) — **zero overlap**. Root
  cause is unchanged from the linked issue doc: the Cloud Run dual-write flag only governs deployment-api's own process,
  not the VM-side heartbeat writer, which reads GCE instance metadata that no real production launcher sets. **Criterion
  1 genuinely fails; criteria 2 and 4 stay untestable as a direct consequence (no `status=running` doc exists to source
  resource stats from or compare for parity); criterion 3's read-path plumbing was already verified passing by slot-12**
  (not re-verified here — a code-path check, not a live-fleet-state check, and not in doubt). **This HALT banner's
  precondition is NOT met — the GCS-write-drop / snapshot-then-delete todos below stay correctly BLOCKED.** Unblocking
  needs the fix + soak tracked in the linked issue doc's own todos (project-metadata fallback for
  `DEPLOYMENT_REGISTRY_FIRESTORE_DUALWRITE`, then a real soak on non-benchmark production VMs, then a fresh 4-criteria
  re-measurement) — not a re-run of this same measurement. Per the finalize plan's own instruction, `assigned_vm` here
  is intentionally left untouched.

- **2026-07-30 (slot 4, cicd) — soak results in; HALT status updated for next-worker visibility, NOT lifted (per the
  linked issue doc's own P2 todo).** The project-metadata fallback fix shipped (deployment-service@deba676) and its soak
  ran (fresh 2026-07-30 ~03:52 UTC measurement, 5 real non-benchmark production VMs launched via their normal launchers)
  — full detail in
  `/plans/archive/2026_08/issues/deployment_registry_dualwrite_flag_not_propagated_to_vm_launchers_2026_07_30.md`'s soak
  todo. Result: **3 of 4 GO/NO-GO criteria FULLY PASS** with fresh live evidence — (2) resource stats read from
  Firestore (real non-zero cpu/mem/disk on a live, non-reap-created VM), (3) per-VM `/{id}/detail` retrievable from
  Firestore for that same live VM, (4) Firestore doc == GCS blob parity, byte-for-byte, for a live deployment.
  **Criterion (1)'s underlying MECHANISM is confirmed correct** — every freshly-booted VM (including one independent VM
  the soak worker never launched) now writes Firestore with `status=running` and heartbeats advancing every ~60s — but
  literal fleet-wide doc-count parity has NOT yet been reached: only 4 of ~19 currently-`RUNNING` GCE instances were
  Firestore-represented at soak time, because the other ~15 are long-running processes that booted BEFORE the fix landed
  (03:11:34 UTC) and won't re-read the corrected metadata until they cycle (complete/restart). This is the expected
  transient shape of a read-at-boot metadata fallback, not a residual defect — a materially different failure mode than
  the original issue (0/16 overlap with zero working mechanism, not a convergence lag). **Net: criteria 1-4 do not yet
  ALL literally pass this checklist's item-1 bar (doc-count ≈ live-VM count) — this HALT is NOT lifted by this note.**
  The root-cause fix is verified working end-to-end though, so the remaining gap is pure convergence timing, not an open
  defect. **For the next P3 worker/operator**: this HALT can be reconsidered once a follow-up count shows the Firestore
  `status=running` doc count tracking the live fleet as the pre-fix population cycles out (no code work needed — a
  passive wait + a fresh count). Re-verify with fresh measurements at that time; do not reuse this note's or the linked
  issue doc's counts (per this doc's own re-verification convention). The remaining GO/NO-GO items stay
  operator-supervised per this doc's own banner; `assigned_vm` is intentionally left untouched.
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — added `gcs_blob_ops.py` (the `gcs_delete_object`
  wrapper this doc's own "Gotchas" section names as the mandatory delete path).
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-06 (ui tranche, dispatch agt-a6d668)**: KEEP-NA, valid — same as 2026-07-30; explicit
  dated operator HALT (2026-07-14) gated on a 4-item GO/NO-GO checklist not yet fully met; irreversible cutover steps
  stay blocked until the dual-write deploy precondition is satisfied and the full checklist clears.
- **context-scout 2026-08-07**: re-verified context_scope (5 entries) -- all 5 still resolve; unchanged after the
  2026-08-06 na-eligibility-audit reaffirmation (no new named artifacts).
- **na-eligibility-audit 2026-08-07 (ui tranche)**: KEEP-NA, valid — same as 2026-07-30/2026-08-06; the dated operator
  HALT (2026-07-14) on the 4-item GO/NO-GO checklist is still in force (criterion 1 last re-measured 2026-07-30, not yet
  re-checked since); irreversible cutover todos stay correctly blocked.
- **2026-08-08 (ui_satellite_ao_dispatch_batch1_finalize, slot 27) — fresh criterion-1 re-measurement; HALT stays in
  force, and the 2026-07-30 "passive wait + a fresh count" expectation is corrected.** Live Firestore REST query (full
  pagination, `unified-trading-sa`) of the prod `deployments` collection: **2,351 total docs** (1,345 `completed`, 449
  `failed`, **557 `running`**), cross-referenced against **176** currently-`RUNNING` GCE instances
  (`gcloud compute instances list --filter=status=RUNNING`, project `central-element-323112`): only **48 of 176** live
  VMs have a matching `status=running` Firestore doc (27% coverage — still failing, same under-coverage direction as
  2026-07-30's 4/19). **New finding this pass**: the other **509** `status=running` Firestore docs do NOT correspond to
  any currently-running GCE instance, and are not a fresh convergence lag — sampled `last_heartbeat_at` ages: min 0.9h,
  median **102.2h (~4.3 days)**, max 229.3h, with 488/509 aged >24h. Root-caused (read-only, not fixed here):
  `SyncService.reap_stale_deployments()` (`deployment_api/services/sync_service.py:564`) instantiates a GCS-only
  `DeploymentsRegistry` and calls `registry.reap_stale(...)` with zero Firestore reference in that method — confirmed
  via `grep -n firestore deployment_api/services/sync_service.py` (zero hits). So the periodic reaper that transitions a
  dead VM's entry to `failed`/`completed` runs ONLY against the GCS registry; Firestore's copy of `status` updates
  exclusively via the dual-write path on live `register`/`heartbeat`/`complete` API calls, so any VM that disappears
  without ever calling `/complete` (crash, preemption, external termination — the norm for this workspace's SPOT-default
  backfill fleet) leaves its Firestore doc stuck at `status=running` forever. This is NOT a new, separately-scoped
  defect — todo 2 below ("Drop the GCS-write half...Confirm the Phase-0 reaper now operates on the Firestore store")
  already anticipates migrating the reaper to Firestore as part of that same step. The correction is to the 2026-07-30
  note's framing: **criterion 1 will NOT converge via a passive wait alone** — the reap-migration work in todo 2 is a
  load-bearing precondition for the doc-count-parity bar, not an optional add-on discovered after the fact. Criteria 2-4
  not re-measured this pass (no new dual-write deploy has landed since 2026-07-30; re-verify those independently before
  trusting this pass's criterion-1 numbers alongside them). **HALT stays correctly in force.** Per this doc's own
  re-verification convention, do not reuse this note's counts for a future re-measurement — re-run fresh.
- **na-eligibility-audit 2026-08-09 (ui tranche, dispatch agt-eee16e)**: KEEP-NA, valid — re-confirmed; the only change
  since the 2026-08-07 marker is the 2026-08-08 (`ui_satellite_ao_dispatch_batch1_finalize`) criterion-1 re-measurement
  entry above, which refines the diagnosis (509 stale `status=running` docs traced to the GCS-only reaper; criterion-1
  won't converge via passive wait alone) without lifting the HALT. The explicit dated operator HALT (2026-07-14) on the
  4-item GO/NO-GO checklist stays correctly in force; all 4 remaining todos are the gated, sequential,
  irreversible-delete cutover steps this doc's own banner blocks pending that checklist. DEPENDENCY_BLOCKED (root: unmet
  GO/NO-GO checklist, itself gated on a Firestore reaper migration + fleet soak).

## Codex SSOTs

- `/codex/05-infrastructure/gcs-object-operations.md` — GCS object ops via UTL wrappers (the delete rule).
- `/codex/05-infrastructure/deployment-observability.md` — registry SSOT (lineage note added Phase 5).
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — Explicit dated operator
  HALT (2026-07-14) gated on a 4-item GO/NO-GO checklist not yet met (fleet writing Firestore, resource stats from new
  surface, per-VM data retrievable, parity check) — irreversible cutover steps stay blocked until the sibling
  migration-overview doc's dual-write deploy (reclassified this run) clears the precondition.
