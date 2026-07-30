---
doc_type: issue
title:
  Deployment registry Firestore dual-write — flag on deployment-api does NOT reach VM heartbeat writers (GO/NO-GO
  criterion 1 fails)
summary: >-
  Verifying the deployment_registry_firestore_migration_2026_07_14.md P0 todo's 4 GO/NO-GO criteria found criterion 1
  (fleet writing Firestore) genuinely fails: prod Firestore `deployments` has 192 docs, all reap-created
  failed/completed entries, zero `status=running`, zero overlap with the 16 currently-live GCE VMs.
  DEPLOYMENT_REGISTRY_FIRESTORE_DUALWRITE=true on deployment-api's Cloud Run env only governs deployment-api's own
  process (reads + its own reap_stale sweep) — the actual write source (deployment_heartbeat.py, run on each VM) reads
  the flag from GCE instance metadata, and no real production VM launcher passes it.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, deployment-api, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: [deployment-registry, firestore, dual-write, vm-launchers, observability]
related:
  [
    /plans/active/deployment_registry_firestore_migration_2026_07_14.md,
    /plans/active/deployment_registry_firestore_p3_cutover_2026_07_14.md,
  ]
created: 2026-07-30
priority: P2
parent_epic: observability_master
source:
  "slot-12, infra, discovered while verifying deployment_registry_firestore_migration_2026_07_14.md's GO/NO-GO todo,
  2026-07-30"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by:
locked_by:
locked_since:
---

# What I found

`deployment_registry_firestore_migration_2026_07_14.md`'s single todo asked to deploy `deployment-api` carrying the
dual-write flag and "enable `DEPLOYMENT_REGISTRY_FIRESTORE_DUALWRITE=true` ... on the fleet", then verify the 4
published GO/NO-GO criteria. The deploy half is genuinely done: `deployment-api` is live at `uts-shared-deployment-api`
(revision `uts-shared-deployment-api-00332-8gl`, image `deployment-api:acdf634`, Cloud Build
`b99e78c1-f5fe-449a-ab49-01ffd70f7b31` SUCCESS, commit `acdf634187bf7967bd36c983824cb4316a47435d`, descendant of
`utl@bf56debe` + `deployment-api@8e93a82`/`543860c`), and its Cloud Run env carries
`DEPLOYMENT_REGISTRY_FIRESTORE_DUALWRITE=true`.

But that env var **only governs `deployment-api`'s own process** — its reads (`resolve_active_registry` /
`resolve_deployment_by_id` in `registry_reader.py`) and its own `reap_stale()` sweep (`vm_deployments.py:391`,
`DeploymentsRegistry(bucket=DEFAULT_BUCKET)` constructed inside deployment-api's process, so it inherits
deployment-api's env). It does **not** reach the actual write source: the VM-side heartbeat helper
(`deployment-service/scripts/vm/deployment_heartbeat.py`), invoked as a subprocess **on each VM itself**, which
constructs its own `DeploymentsRegistry`/`UnifiedCloudConfig` from **that VM's own process env**. That env is populated
at boot from **GCE instance metadata** via `setup-data-pipeline-vm.sh`'s
`DEPLOYMENT_REGISTRY_FIRESTORE_DUALWRITE=$(_meta DEPLOYMENT_REGISTRY_FIRESTORE_DUALWRITE false)` (default `false`) —
i.e. each VM needs `--metadata=DEPLOYMENT_REGISTRY_FIRESTORE_DUALWRITE=true` at `gcloud compute instances create` time.
Verified: of ~164 `deployment-service/scripts/vm/launch-*.sh` launchers, only `launch-synthetic-benchmark-vm.sh` (a
non-production benchmark launcher) passes this metadata key. Every real production launcher
(mtds/cefi/tradfi-bf/mdps/prediction-live/canonical-migration/af-backfill/…) omits it, so their VMs' heartbeats stay
GCS-only. There is also no single low-risk choke point to fix this centrally: the shared `lc_gcloud_create` helper in
`scripts/vm/lib/launcher_common.sh` (which centrally injects the `managed-by` label) is called by only 4 of the ~164
launchers — the other ~137+ call `gcloud compute instances create` directly with their own hand-built `--metadata`
string.

**Live measurement (2026-07-30, prod Firestore `deployments` collection, via REST API, full pagination)**: 192 docs
total — 189 `status=failed`, 3 `status=completed`, **0 `status=running`**. Cross-checked every doc's `vm_name` against
the 16 currently-`RUNNING` GCE instances (`gcloud compute instances list --filter=status=RUNNING`) — **zero overlap**.
Sampled docs show `createTime == updateTime` (single write, not iterative heartbeats) with `last_heartbeat_at` values
from 2026-07-27 through 2026-07-30 — consistent with these being written exactly once, by deployment-api's own
`reap_stale()` transitioning a stale GCS entry to `failed`/`completed` (which, since deployment-api's env has the flag
on, mirrors that single transition to Firestore) — not by any VM's own live heartbeat loop.

# Why it matters

This blocks the whole P0-unblock todo's own stated GO/NO-GO checklist for
`deployment_registry_firestore_p3_cutover_2026_07_14.md` (the phase that drops the GCS write + deletes the GCS registry
blobs):

1. **Fleet writing Firestore, doc count ≈ live-VM count** — FAILS. 0/16 live VMs represented; Firestore only ever sees a
   VM once it's already reap-marked failed/completed.
2. **Resource stats read from the Firestore surface** — untestable in the current state (compound failure of #1; no
   `status=running` doc exists to source cpu/mem/disk/heartbeat from).
3. **Per-VM `/{id}/detail` retrievable from Firestore** — the read-path plumbing itself PASSES: live-verified
   `GET /api/vm-deployments/049fabc8-97e0-4c65-8516-9f0a0770ae37` against `uts-shared-deployment-api` returns the full
   record sourced from the Firestore-resident (reap-created) entry. Not verified against a currently-live VM (none exist
   in Firestore to test with).
4. **Parity (Firestore doc == GCS blob for N live deployments)** — untestable (no live-status Firestore docs to
   compare).

Net: the GO/NO-GO gate genuinely does not clear. `deployment_registry_firestore_p3_cutover_2026_07_14.md`'s 2026-07-14
operator HALT stays correctly in force — its GCS-delete step must not run. (Its own doc already carries this HALT
banner + a KEEP-NA verdict from the 2026-07-30 na-eligibility-audit; nothing in that doc needs touching.)

# Recommended decision

Enabling dual-write "on the fleet" needs a write-path fix, not just a deployment-api env flip. Two shapes, either is
viable — pick one as its own scoped plan (out of bounds for this verify-only todo, and risky to rush across ~137+
launcher files in one pass):

(a) **Project-level GCE metadata fallback** — set `DEPLOYMENT_REGISTRY_FIRESTORE_DUALWRITE=true` via
`gcloud compute project-info add-metadata` (inherited project-wide unless a VM overrides it), and add a narrow fallback
_specific to this one flag_ in the ~5 `setup-*.sh` scripts that read it today (don't change the generic `_meta()`
helper's behavior for every key — only this flag falls back to `project/attributes/` when `instance/attributes/` is
absent). Smallest blast radius; matches the "typed config, not per-launcher opt-in soup" intent already in the P0 doc's
comments.

(b) **Centralize via `lc_gcloud_create`** (mirrors how `managed-by=deployment-service` is already centrally appended) —
but this only reaches the 4 launchers that already call it; the ~137+ direct-`gcloud`-caller launchers would still need
individual edits (or a first migration onto the shared helper, a much bigger lift).

Recommend (a). Needs its own plan (mechanical once scoped, but touches live production VM-launch infra — deserves its
own QG-verified change + a real soak before P3's checklist is re-run).

## Todos

- [x] ✅ [INFRA] P1. Author + ship the project-metadata fallback (option (a) above): set
      `DEPLOYMENT_REGISTRY_FIRESTORE_DUALWRITE=true` via `gcloud compute project-info add-metadata` on
      `central-element-323112`, and add a `_meta_project()` fallback used ONLY for this one flag in
      `deployment-service/scripts/vm/setup-data-pipeline-vm.sh` + `setup-cefi-live-consolidated-vm.sh` +
      `setup-prediction-live-consolidated-vm.sh` + `setup-data-pipeline-vm-aws.sh` (AWS SSM parameter equivalent, not
      GCE metadata) + `setup-honest-coverage-scheduler.sh` (repo: deployment-service). — deployment-service@deba676.
      GCP: project metadata `DEPLOYMENT_REGISTRY_FIRESTORE_DUALWRITE=true` on `central-element-323112` verified already
      present (`gcloud compute project-info describe --format='value(commonInstanceMetadata.items)'`); a new
      `_meta_project()` helper (instance attribute first, then project-level fallback — never changes the generic
      `_meta()` behavior for any other key) now backs the read in `setup-data-pipeline-vm.sh`,
      `setup-cefi-live-consolidated-vm.sh` (also newly exports the flag in the shared shard-process env block, since
      this VM never read it before), `setup-prediction-live-consolidated-vm.sh` (same). AWS:
      `setup-data-pipeline-vm-aws.sh` now falls back to
      `aws ssm get-parameter --name     /uts/deployment-registry/firestore-dualwrite` (region `ap-northeast-1`) when the
      launcher didn't export the var, defaulting to `false` on any SSM error (parameter absent or access denied) — safe
      no-op today. `setup-honest-coverage-scheduler.sh` is NOT a VM startup script (a one-time
      `gcloud scheduler jobs     create/update` invocation — never runs on a GCE VM, never reads instance/project
      metadata); its two real VM launchers (`launch-honest-coverage-vm.sh`, `launch-measure-honest-coverage-vm.sh`) both
      already point `startup-script-url` at `setup-data-pipeline-vm.sh`, which carries the fix — documented in-file
      rather than force an inapplicable edit. Residual: the AWS SSM parameter
      `/uts/deployment-registry/firestore-dualwrite` does not yet exist — this worker's identity (AWS IAM user
      `ikenna-worker`, static creds on this slot host) has neither `ssm:PutParameter` nor `sts:AssumeRole` on
      `uts-orchestrator-epic-role` (verified: both calls return `AccessDenied`/`AccessDeniedException`), so the
      parameter could not be created from here. See the new P2 todo below.

- [ ] [OPERATOR] P2. Set the AWS SSM parameter `/uts/deployment-registry/firestore-dualwrite=true` (String, region
      `ap-northeast-1`, account `427895769566`) so `setup-data-pipeline-vm-aws.sh`'s new fallback actually resolves to
      `true` instead of its safe `false` default:
      `aws ssm put-parameter --name     /uts/deployment-registry/firestore-dualwrite --value true --type String --region ap-northeast-1 --overwrite`.
      Needs an identity with `ssm:PutParameter` on that resource — either the operator directly, or a session running as
      the ambient AWS orchestrator identity `uts-orchestrator-epic-role` (the human-planning/orchestrator VMs only; AO
      worker slots run as a separate, more narrowly-scoped static IAM user per
      `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`, which does not cover this) (repo: infra,
      AWS-only action — no code change).
- [ ] [REVIEW] P1. Soak: launch a handful of real (non-benchmark) production VMs after the fix ships, confirm their
      heartbeats mirror to Firestore with `status=running` and fresh `last_heartbeat_at` within one heartbeat interval,
      then re-run this doc's 4-criteria measurement (repo: deployment-service / unified-trading-pm — re-verification,
      cite fresh evidence, do not reuse this doc's numbers).
- [ ] [DOC] P2. Once the soak confirms criteria 1-4 all pass, note the clear in
      `deployment_registry_firestore_p3_cutover_2026_07_14.md`'s Progress Log (its own text: don't flip its
      `assigned_vm` — its remaining GO/NO-GO items stay operator-supervised per its own text even once this precondition
      clears) so P3's own next worker knows the HALT can be reconsidered (repo: unified-trading-pm).
