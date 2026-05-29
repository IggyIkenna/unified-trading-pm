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

The watchdog VM startup script attempts to install UTL from a tarball in GCS, but the `pip install` step fails silently
(uses `|| true`) when the old pip can't resolve C-extension wheels without a compiler. The watchdog.py then crashes at
module import time on every cron cycle.

**Evidence**: 562 crash events observed from 2026-05-24 to 2026-05-28. Zero actual scans ran.

**Why this VM is broken**: The launcher (`launch-vm-zombie-watchdog.sh`) was patched to add `pip upgrade --upgrade pip`
before UTL install (fixing the wheel resolution), but this fix was added AFTER the current watchdog VM was launched on
2026-05-24. The running VM's startup script is baked-in at launch time — it has the old broken startup and never got the
fix.

**Scale of damage**: 101 TERMINATED VMs accumulated (9+ days unswept). Breakdown by prefix:

- `mdps-*`: 33 VMs (oldest: 2026-05-19)
- `gcs-migration-bundle-*`: 31 VMs (oldest: 2026-05-19)
- `cefi-*`: 20 VMs (oldest: 2026-05-19)
- `mtds-*`: 8 VMs (oldest: 2026-05-07)
- `amm-golden-*`: 5 VMs (oldest: 2026-05-13)
- `instr-backfill-*`: 2 VMs
- `tradfi-bf-*` + `tradfi-fwd-*`: 2 VMs

## Root cause hypothesis

**Primary**: Option (d) — script not actually running. The `startup-script` metadata embedded in the VM at launch time
crashes at Python import (`line 76`) before any actual scanning occurs. The watchdog VM is RUNNING but the watchdog
Python process is in a crash-loop, never scanning any VMs.

**Secondary** (contributing): The `launch-vm-zombie-watchdog.sh` pip install section used `|| true` to suppress errors —
so a failed UTL install produces no visible VM-launch error, the watchdog VM boots successfully, and the cron appears to
be configured. The only evidence of failure is in GCP serial console / serial port logs (not surfaced to monitoring).

**Not the root cause**:

- (a) TTL too generous: irrelevant — zero scans run. No TERMINATED status filtering (watchdog only kills RUNNING VMs
  anyway).
- (b) Only sweeps certain lifecycle classes: irrelevant — no scans ran.
- (c) Silent failures on dependent disks/IAM: not the issue — GCS reads succeed fine. The failure is before any GCS
  access.

## Recommended fix

**One-step operator fix**: Relaunch the watchdog VM. The launcher already has the corrected startup script (pip upgrade
before UTL install, per 2026-05-24→27 incident fix noted in line 167 of `launch-vm-zombie-watchdog.sh`). The current
broken VM just needs to be replaced.

```bash
# Kill the broken watchdog VM
gcloud compute instances delete vm-zombie-watchdog-20260524-191752 \
  --zone=asia-northeast1-c --project=central-element-323112 --quiet

# Relaunch from the already-fixed launcher
bash deployment-service/scripts/vm/launch-vm-zombie-watchdog.sh
```

**Estimated time to fix**: <5 minutes operator action. No code change needed — the launcher is already correct.

**Optional hardening** (not urgent, file as separate P3):

- Add a smoke-test to the launcher: after VM boots, wait 2 min and check serial console for `ModuleNotFoundError` — exit
  1 if found.
- Add a Cloud Monitoring alert on
  `resource.type="gce_instance" AND textPayload:"ModuleNotFoundError" AND resource.labels.instance_id~"zombie-watchdog"`.

## Manual cleanup executed today

**Cleanup date**: 2026-05-28 UTC (this session) **Operator authorization**: confirmed in task prompt

| Prefix                    | Count   | Notes                                         |
| ------------------------- | ------- | --------------------------------------------- |
| `mdps-*`                  | 33      | All TERMINATED ≥24h, no lifecycle_class label |
| `gcs-migration-bundle-*`  | 31      | All TERMINATED ≥24h, no lifecycle_class label |
| `cefi-*`                  | 20      | All TERMINATED ≥24h, no lifecycle_class label |
| `mtds-*`                  | 8       | All TERMINATED ≥24h                           |
| `amm-golden-*`            | 5       | All TERMINATED ≥24h                           |
| `instr-backfill-*`        | 2       | All TERMINATED ≥24h                           |
| `tradfi-bf-*`             | 1       | TERMINATED ≥24h                               |
| `tradfi-fwd-daily-cron-*` | 1       | TERMINATED ≥24h                               |
| **Total deleted**         | **101** | All succeeded — zero failures                 |

**Skipped (5 VMs)**: `strategy-paper-carry-staked-basis-*` — classified `LONG_LIVED_LIVE` in
`vm_zombie_watchdog.py:VM_PREFIX_TO_BUCKET` (`strategy-paper-` →
`VmPrefixSpec(bucket=None, lifecycle_class=LifecycleClass.LONG_LIVED_LIVE)`). These are terminated paper-trade VMs —
operator should review if they should be deleted or relaunched.

**Cleanup log**: `/tmp/vm_cleanup_log.txt` (local to agent session)

## Why it matters

At 19 RUNNING VMs currently vs 101 TERMINATED, the watchdog was supposed to prevent this accumulation. Each TERMINATED
VM retains its disk attachments (billable storage) until deleted. 101 TERMINATED × average ~10GB persistent disk = ~1TB
of billing until cleanup. With watchdog down since 2026-05-24, any future batch job that fails to self-delete will also
accumulate.

The `strategy-paper-*` VMs (LONG_LIVED_LIVE) legitimately stay TERMINATED until the operator re-promotes — those are not
in scope for the watchdog anyway.

## Recommended decision

1. **Immediate (operator, <5 min)**: relaunch watchdog with the 2 commands above.
2. **Review `strategy-paper-*` VMs**: 5 terminated paper-trade VMs from 2026-05-18/19 — determine if these should be
   deleted or are awaiting re-promotion.
3. **P3 hardening**: add boot-time smoke-test to launcher (separate issue if desired).

## Status log

- 2026-05-28 11:26 UTC — harsh-main executed the relaunch: deleted `vm-zombie-watchdog-20260524-191752`, launched
  `vm-zombie-watchdog-20260528-112656` (asia-northeast1-c, e2-small, 10.146.0.2 / 34.85.46.246, interval=300s). VM
  RUNNING. T+10min verification still pending — should confirm first sweep event lands by 11:36 UTC.
- 2026-05-28 — operator review pending on the 5 `strategy-paper-*` TERMINATED VMs (decision 2 above).
- 2026-05-28 14:55 UTC — ikenna-slot-1 confirmed the 11:26 watchdog STILL crash-looped past the build-essential fix, on
  two further failures: (1) `cloud-providers.yaml` SSOT missing on watchdog VM (UTL `_load_cloud_providers_yaml` probed
  only relative paths; no override env); (2) once yaml staged, `_substitute_env_vars` raised on unset
  `${GCP_PROJECT_ID}` / `${DEPLOYMENT_ENV_SHORT}` template vars. Shipped `deployment-service@f0c81cd` (yaml staging via
  deployment-service tarball + `UNIFIED_TRADING_CLOUD_PROVIDERS_YAML` export) and `@9e31b33` (export `GCP_PROJECT_ID` /
  `PROJECT_ID` / `DEPLOYMENT_ENV_SHORT=prd`). A third fix `@c8d38b6`/`@53457ba` pip-installs `/tmp/dep-src` so
  `_backup_vm_logs_before_kill` can `import deployment_service.deployments_registry` (previously logged
  `Pre-kill log backup failed: No module named deployment_service` on every reap). Current watchdog
  `vm-zombie-watchdog-20260528-155035` healthy at 15:01:54 UTC: `Watchdog summary: 5 alive / 0 zombie / 1 too_young`.

## Follow-ups discovered during the fix (2026-05-28)

While walking the 9 `cefi-{bybit,deribit,hyperliquid,kraken-spot,okx-futures}-*-heavy-20260524/25-*` zombies down, the
2021-heavy sibling (same launch batch, `RUN_TS=20260525-021423`) succeeded (rc=0, self-deleted) but the 2024-heavy never
uploaded `run.log` at all → pipeline died in early bootstrap, before the periodic uploader started. Launcher comment at
`launch-cefi-sharded-backfill.sh:311-317` calls out exactly this failure mode: stale consolidated
availability_index.parquet → `ManifestReader` fallback → loads all shards → OOM-kill at startup (rc=137). With the
watchdog crash-looping and the manifest-consolidator infra possibly degraded in the same window, the mitigation env
(`MANIFEST_CONSOLIDATED_STALENESS_SEC=86400`) may not have been sufficient.

- [x] ✅ [INFRA] P1. Audit manifest-consolidator state during 2026-05-24 → 2026-05-28 watchdog-down window. **Done
      2026-05-28** — see audit findings below. **OOM-fallback hypothesis NOT supported.** During the cefi-heavy launch
      window (2026-05-24 22:00 → 2026-05-25 09:00 UTC), the env-tiered `uts-prod-manifest-consolidator-market-data-cefi`
      job had **0 errors** in Cloud Logging (`severity>=ERROR`); the LEGACY job `…-market-data-cefi-legacy` had 18
      errors in the same window (writes to the flat bucket `market-data-tick-cefi-central-element-323112`, NOT the
      env-tiered PRD bucket the heavy backfills wrote to). Current `availability_index.parquet` in
      `market-data-tick-cefi-prd-central-element-323112/_index/` is fresh (mtime 2026-05-28 20:42 UTC — minutes ago).
      Conclusion: PRD consolidator was healthy during the window; `MANIFEST_CONSOLIDATED_STALENESS_SEC=86400` mitigation
      was NOT defeated by stale index → the 9 zombies died for a different reason in early bootstrap. Root cause
      downgraded from "OOM on stale-fallback" to "early-bootstrap crash (apt/tarball/pip) before vm-exec-with-gcs-tee.sh
      launched" — no serial console preserved, so the exact apt/pip line is unknown. Audit-only finding for legacy
      consolidator (39 errors over 5 days = 0.5% failure rate, not breaking any flow we use today) → tracked in
      [legacy-flat-cefi-consolidator-failure-rate-2026-05-28](TBD if action needed).
- [x] ✅ [INFRA] P1. Harden OOM mitigation for cefi-heavy backfills. **Shipped 2026-05-28 option (b)** —
      `deployment-service@7add531`. Added shell-level preflight in `setup-data-pipeline-vm.sh`: when
      `VM_SERVICE=market_tick_data_service` + `VM_OPERATION=download` + asset_group in {cefi,defi,tradfi,sports,pred},
      `gsutil ls -L` the bucket's `_index/availability_index.parquet` and compare mtime against
      `MANIFEST_CONSOLIDATED_STALENESS_SEC` budget (default 86400s). If stale beyond budget → log typed diagnosis + exit
      78 (EX_CONFIG). The EXIT trap from `334784c` catches and self-deletes with forensics to
      `vm-logs/<vm>/vm-setup.log` + `SETUP_EXIT_STATUS`. Scoped narrowly (other VMs unaffected). Picked option (b) over
      recommended option (a) because option (a) touches the UTL `read_availability_index` SSOT that many cross-repo
      consumers depend on — that change deserves a focused PR + cross-repo consumer audit and isn't worth bundling with
      incident response. Option (a) remains a future hardening — file separately if/when an MTDS slot has the cycles.
      Option (c) (raise heavy machine type) not pursued — no measured evidence the current type is wrong.
- [x] ✅ [INFRA] P0. Make VM self-delete fire on rc≠0 too. **Done 2026-05-28** — shipped `deployment-service@334784c`.
      Real gap was not in `vm-exec-with-gcs-tee.sh:277` (which already fires on rc≠0 unconditionally on
      `VM_SHUTDOWN_ON_COMPLETION=true`) but in `setup-data-pipeline-vm.sh` which uses `set -euo pipefail` with no EXIT
      trap — any apt/tarball/pip failure in early bootstrap exits the script before `_launch_with_tee` runs, so the
      wrapper-level self-delete never gets a chance. Fix: register an EXIT trap at the top of
      `setup-data-pipeline-vm.sh` that on non-zero exit uploads the setup log + `SETUP_EXIT_STATUS` to
      `gs://CODE_BUCKET/vm-logs/<vm>/` for forensics, then schedules
      `gcloud compute instances delete --delete-disks=all` (gated on `VM_SHUTDOWN_ON_COMPLETION=true` to preserve
      long-lived live VMs). Disarm the trap inside `_launch_with_tee` after successful `nohup`-launch — from that point
      on, the wrapper owns lifecycle and a later non-zero exit of the setup script must NOT delete the running pipeline.
      Defense in depth: the zombie-watchdog still catches anything this trap misses (e.g. SIGKILL of the setup script
      itself, network-namespace loss).

## Audit findings (2026-05-28 — manifest-consolidator window 2026-05-23 → 2026-05-28)

Cloud Logging `severity>=ERROR` count per Cloud Run Job, 5-day window:

| Job                                                            | Errors | Notes                                                        |
| -------------------------------------------------------------- | -----: | ------------------------------------------------------------ |
| `uts-prod-manifest-consolidator-market-data-cefi-legacy`       |     39 | flat bucket — NOT used by env-tiered cefi-heavy backfills    |
| `uts-prod-manifest-consolidator-instruments-tradfi-legacy`     |      5 | flat instruments bucket                                      |
| `uts-prod-manifest-consolidator-market-data-defi-legacy`       |      4 | flat defi bucket                                             |
| `uts-prod-manifest-consolidator-instruments-prediction-legacy` |      4 | flat instruments-prediction                                  |
| `uts-prod-manifest-consolidator-instruments-prediction`        |      4 | env-tiered instruments-prediction                            |
| `uts-prod-manifest-consolidator-market-data-prediction`        |      3 | env-tiered                                                   |
| `uts-prod-manifest-consolidator-instruments-tradfi`            |      3 | env-tiered                                                   |
| `uts-prod-manifest-consolidator-instruments-cefi`              |      3 | env-tiered                                                   |
| `uts-prod-manifest-consolidator-market-data-tradfi`            |      2 | env-tiered                                                   |
| `uts-prod-manifest-consolidator-market-data-sports-legacy`     |      2 | flat                                                         |
| `uts-prod-manifest-consolidator-instruments-defi-legacy`       |      2 | flat                                                         |
| `uts-prod-manifest-consolidator-instruments-defi`              |      2 | env-tiered                                                   |
| `uts-prod-manifest-consolidator-market-data-prediction-legacy` |      1 | flat                                                         |
| `uts-prod-manifest-consolidator-market-data-defi`              |      1 | env-tiered                                                   |
| **`uts-prod-manifest-consolidator-market-data-cefi`**          |  **0** | **env-tiered cefi — where the 9 dead heavy backfills wrote** |

Cefi-heavy launch window (2026-05-24 22:00 → 2026-05-25 09:00 UTC) tight-band slice: env-tiered cefi 0 errors / legacy
cefi 18 errors. `availability_index.parquet` mtime in `gs://market-data-tick-cefi-prd-central-element-323112/_index/`:
fresh (current update 2026-05-28 20:42 UTC, well within consolidator's 1-min cadence). Conclusion: the env-tiered
consolidator path was healthy; `MANIFEST_CONSOLIDATED_STALENESS_SEC=86400` mitigation was not defeated by index
staleness. The 9 zombies died upstream of the Python pipeline entirely — in `setup-data-pipeline-vm.sh` bootstrap.

The 39 legacy-cefi errors are not in any May-23 critical path (legacy flat bucket isn't read by the carry/dispersion
strategies) but should be diagnosed at some point for hygiene. Not filing as a separate issue doc yet — likely
investigation will fold into a broader legacy-bucket retirement plan once env-tiered cutover is verified end-to-end.
