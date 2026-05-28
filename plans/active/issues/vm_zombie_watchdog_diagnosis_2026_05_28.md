---
title: "vm_zombie_watchdog crash-loop: 101 TERMINATED VMs accumulate due to ModuleNotFoundError at boot"
created: 2026-05-28
author: harsh-bg-cleanup-subagent
source:
  - deployment-service/scripts/vm/vm_zombie_watchdog.py
  - deployment-service/scripts/vm/launch-vm-zombie-watchdog.sh
  - /tmp/vm_cleanup_log.txt
locked_by: live-defi-rollout
---

## What I found

**Root cause confirmed via live GCP logs** on `vm-zombie-watchdog-20260524-191752` (the currently RUNNING watchdog VM):

```
ModuleNotFoundError: No module named 'unified_trading_library'
File "/tmp/watchdog.py", line 76, in <module>
    from unified_trading_library import resolve_bucket_name
```

The watchdog VM startup script attempts to install UTL from a tarball in GCS, but the `pip install` step fails silently (uses `|| true`) when the old pip can't resolve C-extension wheels without a compiler. The watchdog.py then crashes at module import time on every cron cycle.

**Evidence**: 562 crash events observed from 2026-05-24 to 2026-05-28. Zero actual scans ran.

**Why this VM is broken**: The launcher (`launch-vm-zombie-watchdog.sh`) was patched to add `pip upgrade --upgrade pip` before UTL install (fixing the wheel resolution), but this fix was added AFTER the current watchdog VM was launched on 2026-05-24. The running VM's startup script is baked-in at launch time — it has the old broken startup and never got the fix.

**Scale of damage**: 101 TERMINATED VMs accumulated (9+ days unswept). Breakdown by prefix:
- `mdps-*`: 33 VMs (oldest: 2026-05-19)
- `gcs-migration-bundle-*`: 31 VMs (oldest: 2026-05-19)
- `cefi-*`: 20 VMs (oldest: 2026-05-19)
- `mtds-*`: 8 VMs (oldest: 2026-05-07)
- `amm-golden-*`: 5 VMs (oldest: 2026-05-13)
- `instr-backfill-*`: 2 VMs
- `tradfi-bf-*` + `tradfi-fwd-*`: 2 VMs

## Root cause hypothesis

**Primary**: Option (d) — script not actually running. The `startup-script` metadata embedded in the VM at launch time crashes at Python import (`line 76`) before any actual scanning occurs. The watchdog VM is RUNNING but the watchdog Python process is in a crash-loop, never scanning any VMs.

**Secondary** (contributing): The `launch-vm-zombie-watchdog.sh` pip install section used `|| true` to suppress errors — so a failed UTL install produces no visible VM-launch error, the watchdog VM boots successfully, and the cron appears to be configured. The only evidence of failure is in GCP serial console / serial port logs (not surfaced to monitoring).

**Not the root cause**:
- (a) TTL too generous: irrelevant — zero scans run. No TERMINATED status filtering (watchdog only kills RUNNING VMs anyway).
- (b) Only sweeps certain lifecycle classes: irrelevant — no scans ran.
- (c) Silent failures on dependent disks/IAM: not the issue — GCS reads succeed fine. The failure is before any GCS access.

## Recommended fix

**One-step operator fix**: Relaunch the watchdog VM. The launcher already has the corrected startup script (pip upgrade before UTL install, per 2026-05-24→27 incident fix noted in line 167 of `launch-vm-zombie-watchdog.sh`). The current broken VM just needs to be replaced.

```bash
# Kill the broken watchdog VM
gcloud compute instances delete vm-zombie-watchdog-20260524-191752 \
  --zone=asia-northeast1-c --project=central-element-323112 --quiet

# Relaunch from the already-fixed launcher
bash deployment-service/scripts/vm/launch-vm-zombie-watchdog.sh
```

**Estimated time to fix**: <5 minutes operator action. No code change needed — the launcher is already correct.

**Optional hardening** (not urgent, file as separate P3):
- Add a smoke-test to the launcher: after VM boots, wait 2 min and check serial console for `ModuleNotFoundError` — exit 1 if found.
- Add a Cloud Monitoring alert on `resource.type="gce_instance" AND textPayload:"ModuleNotFoundError" AND resource.labels.instance_id~"zombie-watchdog"`.

## Manual cleanup executed today

**Cleanup date**: 2026-05-28 UTC (this session)
**Operator authorization**: confirmed in task prompt

| Prefix | Count | Notes |
|--------|-------|-------|
| `mdps-*` | 33 | All TERMINATED ≥24h, no lifecycle_class label |
| `gcs-migration-bundle-*` | 31 | All TERMINATED ≥24h, no lifecycle_class label |
| `cefi-*` | 20 | All TERMINATED ≥24h, no lifecycle_class label |
| `mtds-*` | 8 | All TERMINATED ≥24h |
| `amm-golden-*` | 5 | All TERMINATED ≥24h |
| `instr-backfill-*` | 2 | All TERMINATED ≥24h |
| `tradfi-bf-*` | 1 | TERMINATED ≥24h |
| `tradfi-fwd-daily-cron-*` | 1 | TERMINATED ≥24h |
| **Total deleted** | **101** | All succeeded — zero failures |

**Skipped (5 VMs)**: `strategy-paper-carry-staked-basis-*` — classified `LONG_LIVED_LIVE` in `vm_zombie_watchdog.py:VM_PREFIX_TO_BUCKET` (`strategy-paper-` → `VmPrefixSpec(bucket=None, lifecycle_class=LifecycleClass.LONG_LIVED_LIVE)`). These are terminated paper-trade VMs — operator should review if they should be deleted or relaunched.

**Cleanup log**: `/tmp/vm_cleanup_log.txt` (local to agent session)

## Why it matters

At 19 RUNNING VMs currently vs 101 TERMINATED, the watchdog was supposed to prevent this accumulation. Each TERMINATED VM retains its disk attachments (billable storage) until deleted. 101 TERMINATED × average ~10GB persistent disk = ~1TB of billing until cleanup. With watchdog down since 2026-05-24, any future batch job that fails to self-delete will also accumulate.

The `strategy-paper-*` VMs (LONG_LIVED_LIVE) legitimately stay TERMINATED until the operator re-promotes — those are not in scope for the watchdog anyway.

## Recommended decision

1. **Immediate (operator, <5 min)**: relaunch watchdog with the 2 commands above.
2. **Review `strategy-paper-*` VMs**: 5 terminated paper-trade VMs from 2026-05-18/19 — determine if these should be deleted or are awaiting re-promotion.
3. **P3 hardening**: add boot-time smoke-test to launcher (separate issue if desired).
