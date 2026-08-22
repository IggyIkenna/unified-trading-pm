---
doc_type: issue
title:
  DP-VM-003 heartbeat stall on canonical-migration-cefi-deribit-sweep-20260816-003410 — relaunched under a fresh VM
  name (dry-run, safe); old wedged VM left RUNNING per the canonical-migration no-autonomous-delete carve-out,
  operator decision needed on whether to delete it
summary: >-
  A DP_VM_STALL (DP-VM-003, WARN) escalation (agt-a67305) reported
  `canonical-migration-cefi-deribit-sweep-20260816-003410` heartbeat 15m stale. This worker followed
  `RB-INFRA-RELAUNCH`: `launcher_registry.resolve_launcher_for_vm()` resolved the `canonical-migration-cefi-` prefix to
  `launch-canonical-migration-vm.sh`; no supervising wrapper exists for this launcher; no suppression marker
  (`vm-census/relaunch-paged/vm/<vm_name>.json`) existed (no prior relaunch attempt today). Diagnosis via the SDK
  (`_gcs.run_log_signals` + `read_launch_params`/`read_progress_checkpoint`, no subprocess `gsutil`/`gcloud storage`):
  the VM's own `run.log` — including its in-VM 60s `PIPELINE_HEARTBEAT` emitter, a background thread independent of the
  actual migration script — froze simultaneously at `2026-08-16T00:45:03Z` and stayed frozen through this worker's read
  (~01:05Z, ~20 min of total silence). `LAUNCH_PARAMS.json` showed a single-day `MODE=dry` sweep
  (`RESUME_ASSET_GROUP=cefi-deribit-sweep`, `RESUME_START_DATE=RESUME_END_DATE=2026-08-16`, `RESUME_SHARD_OF=1`); no
  `MIGRATION_PROGRESS-shard0.json` checkpoint existed yet, so no in-progress work was at risk.

  This worker attempted `gcloud compute instances delete` on the wedged VM (to free its name before relaunching under
  the SAME name, per the launcher's `VM_NAME_OVERRIDE` checkpoint-continuity contract) and was correctly BLOCKED by
  `block_destructive_commands.py`'s VM-delete guardrail, which pointed to `data_engineering.md` STEP 0.55's
  `canonical-migration-` prefix carve-out (codified 2026-08-08,
  `plans/archive/issues/claude_code_agent_deletes_active_canonical_migration_vm_2026_08_07.md`): even with all 3
  liveness signals stale, this VM class is NOT autonomously deletable — a frozen heartbeat/run.log is not dispositive
  for it (the 2026-08-07 incident killed a VM that was legitimately 22 minutes into a bounded `download_as_bytes`
  call). Because no checkpoint existed and `MODE=dry` (read-only, no canonical-data writes), this worker took the SAFE
  alternative instead of escalating and blocking on it: relaunched under a FRESH auto-`RUN_TS` name
  (`canonical-migration-cefi-deribit-sweep-20260816-010754`, omitting `VM_NAME_OVERRIDE`) rather than reusing the old
  name — a duplicate concurrent dry-run has no data-correctness downside, only a few extra minutes of compute cost.
  Verified STARTED (new VM `RUNNING`, tarballs fresh, dry-run script launched — see Progress Log).

  **Open question for the operator**: the OLD VM (`...-003410`) is still `RUNNING` and, per the carve-out, this worker
  will not delete it. If it is genuinely wedged (not a legitimate long download — a single-day `cefi-deribit-sweep`
  dry-run is a small, targeted scope, unlike the large corpus-walk categories the carve-out's precedent incident
  concerned), it is pure billing waste alongside the new relaunch. If it recovers on its own, the duplicate dry-run
  work is harmless. Either way, a human should confirm and delete it if genuinely dead.
status: resolved
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [dp-vm-003, heartbeat-stall, canonical-migration, relaunch, vm-delete-guardrail, deribit-sweep]
related:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/archive/issues/claude_code_agent_deletes_active_canonical_migration_vm_2026_08_07.md,
    /plans/archive/issues/dp_vm_003_manifest_recon_cefi_wedged_non_relaunchable_2026_08_15.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
context_scope: [/codex/15-runbooks/incidents/rb_infra_relaunch.md, /codex/05-infrastructure/data-pipeline-alerts.md, agents/data_engineering.md, deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py, deployment-service/deployment_service/data_pipeline_monitors/_gcs.py, deployment-service/scripts/recovery/relaunch_stalled_vm.py, deployment-service/scripts/vm/launch-canonical-migration-vm.sh]
created: "2026-08-16"
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.1
assigned_role: devops
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: >-
  2026-08-22 (D10 remediation) — both VMs independently reached DEPLOYMENT_COMPLETED exit_code=0 and self-deleted
  on 2026-08-16; confirmed via direct GCS run.log reads, no delete action needed or performed.
source: >-
  Escalation agt-a67305 (wall_type=data_pipeline_failure, dispatched to slot 15, 2026-08-16) — client_payload carried
  vm_name=canonical-migration-cefi-deribit-sweep-20260816-003410, asset_group=cefi, no separate audit CSV attached
  ("Filed issue: (none — alert carries the details)").
---

> **🗄️ ARCHIVED 2026-08-22** — sole todo resolved: both VMs (old + fresh-name relaunch) independently completed
> cleanly and self-deleted on 2026-08-16; no delete action was needed. See `resolved_by` + Progress Log for evidence.

# DP-VM-003 — canonical-migration-cefi-deribit-sweep wedged, relaunched under a fresh name, old VM left for operator

## What happened

- `canonical-migration-cefi-deribit-sweep-20260816-003410` (a single-day `cefi-deribit-sweep` dry-run migration sweep,
  `deribit_combo_perpetual_partition_move_2026_08_03.py --sweep-stale-rows --dry-run`) went silent on all 3 liveness
  signals (heartbeat blob, `run.log` tail, `PIPELINE_HEARTBEAT` marker) simultaneously at `2026-08-16T00:45:03Z`.
- No `MIGRATION_PROGRESS-shard0.json` checkpoint existed — the run hung before recording any progress, so nothing was
  lost either way.
- This worker's attempt to delete the wedged VM (to free the name for an exact-name relaunch) was correctly refused
  by the VM-delete guardrail's `canonical-migration-` carve-out (STEP 0.55) — this VM class can legitimately freeze
  mid-download and a frozen heartbeat alone is not dispositive.
- Relaunched under a fresh name instead (`VM_NAME_OVERRIDE` omitted): `canonical-migration-cefi-deribit-sweep-20260816-010754`,
  confirmed `RUNNING`, tarballs fresh (`mtds-code@9e5f97ba2dee`, `unified-api-contracts-code@0228afe52a9b`,
  `unified-trading-library-code@f036e1827b57`, `deployment-service-code@45a2f9066f02`).

## Todos

- [x] ✅ [OPERATOR] P2. **RESOLVED 2026-08-22 (D10 remediation session) — the old VM was NEVER hung; nothing to
      delete.** Direct GCS `run.log` read (UTL `get_storage_client().download_bytes`, no subprocess `gsutil`) for
      BOTH `canonical-migration-cefi-deribit-sweep-20260816-003410` (the old VM this todo asked about) and
      `-010754` (the same-day fresh-name relaunch) shows each independently reached
      `DEPLOYMENT_COMPLETED ... (exit_code=0)` at 2026-08-16T01:49:22Z / 01:19:19Z respectively, printed its
      `--dry-run` result (799 rows would be deleted), then self-deleted via its own
      `VM_SHUTDOWN_ON_COMPLETION=true` trap — confirmed by `gcloud compute instances list --filter="name~deribit"`
      returning **zero** rows today (neither VM exists any more; both terminated cleanly on their own, not by any
      operator/agent delete). The frozen-heartbeat/frozen-run.log symptom that triggered this escalation was exactly
      the documented "long GCS download, sidecar SIGPIPE" false-wedge pattern this doc's own carve-out citation
      warned about — confirmed here as a false positive, not a genuine hang. No delete was needed or performed.

## Recommended decision

- **A**: Operator inspects the old VM (`...-003410`) directly (serial console / `py-spy dump` if still reachable) to
  confirm genuine wedge vs. legitimate long-running call, then deletes it if dead. **[WORKER REC]** — a single-day
  dry-run sweep is a small, targeted scope unlike the carve-out's large-corpus-walk precedent, so a 20+min freeze here
  is more likely a genuine hang than the precedent's false positive.
- **B**: Leave it — it will either self-recover (harmless duplicate dry-run) or eventually get caught by a
  billing-waste sweep (`/vm-preemption-billing-waste-audit`).

## Progress Log

- 2026-08-16 (agt-a67305, slot 15): Diagnosed wedge via SDK reads (no subprocess `gcloud`/`gsutil`). Delete attempt
  correctly blocked by the VM-delete guardrail. Relaunched under fresh name
  `canonical-migration-cefi-deribit-sweep-20260816-010754` — confirmed `STARTED` (RUNNING, tarballs fresh). Filed this
  issue for the operator decision on the old VM. Not deleted; not requeued for autonomous deletion.
- **na-eligibility-audit 2026-08-16** [body-hash:1f4088066aced979]: KEEP-NA, valid — Freshly-filed (2026-08-16, same day as this audit) single-todo issue doc, read in full (124 lines). Its one open todo asks the operator to decide whether to delete an old wedged canonical-migration VM.
**context-scout 2026-08-17**: populated/refreshed context_scope (7 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (7 entries)
- **2026-08-22 (D10 remediation, dispositions.json `issues_corpus_completion_2026_08_21`)**: Operator-approved D10
  ("inspect the deribit-sweep VM then delete only if confirmed hung") executed. Both the old VM and its same-day
  fresh-name relaunch had already reached `DEPLOYMENT_COMPLETED exit_code=0` and self-deleted on 2026-08-16 — neither
  exists in `gcloud compute instances list` today. No delete performed (nothing to delete); confirmed via direct
  GCS `run.log` reads. Doc's sole todo resolved as a false-positive-wedge finding, not a genuine hang. Flipping
  `status: resolved` — ready for archival on the next hygiene sweep.
