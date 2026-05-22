---
name: infrastructure_master_audit_instructions
type: audit-instructions
epic: infrastructure_master
assigned_vm: vm-cross-cutting
tier: L4
last_updated: 2026-05-22
---

# Infrastructure Master — Audit Instructions

## Epic Scope

VM lifecycle management (`lifecycle_class`, zombie watchdog, zone policy), tarballs (`create-code-tarballs.sh`), per-tab
worktrees, GCS object operations (UTL library only, no subprocess), bucket SSOT (`resolve_bucket_name()`), cloud
bootstrap. Hard rules: asia-northeast1-c default zone; no cross-region fallback; no subprocess gsutil/gcloud.

Codex SSOTs: `codex/05-infrastructure/vm-tarball-deployment.md`, `codex/05-infrastructure/per-tab-worktrees.md`,
`codex/05-infrastructure/gcs-object-operations.md`, `plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md`

## Triggers

- Monthly (minimum cadence)
- After any VM topology change (new VM prefix, VM removed)
- After any new prefix added to `VM_PREFIX_TO_BUCKET` in `vm_zombie_watchdog.py`
- When bucket name SSOT plan advances a phase
- After operator laptop onboarding or cron re-setup

## Checklist

- [ ] (a) **All VM_PREFIX_TO_BUCKET entries have lifecycle_class**: every non-`None` entry is a `VmPrefixSpec` with
      `lifecycle_class=LifecycleClass.<EPHEMERAL_BATCH|...>`. Read:
      `deployment-service/scripts/vm/vm_zombie_watchdog.py` — verify no raw bucket strings without lifecycle_class

- [ ] (b) **Experiment VM names include run_id**: `EPHEMERAL_EXPERIMENT` VMs use pattern `{prefix}{run_id}-{ts}`. Read:
      relevant VM launch scripts in `deployment-service/scripts/vm/` — verify naming for exp- prefixes

- [ ] (c) **Zone default is asia-northeast1-c, no cross-region fallback**: all `gcloud compute instances create`
      commands default to `asia-northeast1-c` with stockout fallback only to `-b` or `-a` (same region). Grep:
      `rg "us-central1\|us-east1\|europe-" deployment-service/scripts/vm/ --include="*.sh"` — should be 0 hits

- [ ] (d) **No subprocess gsutil/gcloud for per-object ops**: all per-object GCS work uses UTL library. Grep:
      `rg "subprocess.*gsutil|subprocess.*gcloud" --include="*.py"` — should be 0 hits in migration scripts and VM
      launch scripts (CLI tooling may use gsutil, but not per-object loops)

- [ ] (e) **resolve_bucket_name() for all bucket lookups — QG STEP 5.69**: no inline `gs://` f-strings. Run: QG STEP
      5.69 passes workspace-wide

- [ ] (f) **verify-slot-host-symmetry.sh exits 0**: operator laptop has both crons installed and ran within 10 min. Run:
      `bash unified-trading-pm/scripts/verify-slot-host-symmetry.sh`

- [ ] (g) **Orphan-ping audit cron active**: Cloud Scheduler job `uts-prod-orphan-ping-audit` is ENABLED in
      `central-element-323112` / `asia-northeast1`. Check:
      `gcloud scheduler jobs describe uts-prod-orphan-ping-audit --location=asia-northeast1`

## Success Criteria

- All 7 checklist items GREEN
- No zombie VMs (zombie watchdog returns empty list)
- verify-slot-host-symmetry.sh exits 0
- QG exits 0 for deployment-service

## Output Format

Result file at `plans/audit/results/infrastructure_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
