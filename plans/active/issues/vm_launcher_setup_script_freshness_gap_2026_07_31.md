---
doc_type: issue
title:
  "139 of 143 VM launchers call `gcloud compute instances create` directly, bypassing `lc_verify_setup_script_freshness`
  entirely — the fleet-wide preemption-signal systemd unit's own freshness is unverified"
summary: >-
  Found while hardening `launch-api-football-backfill-vm.sh`'s two best-effort GCS writes
  (infra_satellite_ao_dispatch_batch1_2026_07_26.md). A live sweep of every af-backfill preemption confirmed via `gcloud
  compute operations list` (5 events, 2026-07-25..2026-07-31) found the `PREEMPTED` marker missing 5/5 times — despite
  af-backfill booting via the shared `setup-data-pipeline-vm.sh` startup-script seam, which (per its own 2026-07-20/21
  comments) installs a `uts-preemption-signal.service` systemd unit specifically to write that marker fleet-wide, with
  its own 2-attempt retry + tight timeouts. Investigating why an already-hardened mechanism still misses 5/5 surfaced a
  structural gap: `lc_verify_setup_script_freshness` (the guard that would catch a stale copy of
  `setup-data-pipeline-vm.sh` on GCS) is only invoked automatically by `lc_gcloud_create` — and only 4 of 143 launcher
  scripts actually call `lc_gcloud_create`. The other 139 (including af-backfill, before this session's fix) call
  `gcloud compute instances create` directly and never invoke the freshness guard at all, despite `launcher_common.sh`'s
  own doc-comment claiming "every caller of lc_gcloud_create (~80 launchers) inherits it automatically" — that comment
  is itself stale; the real number is 4. This session could NOT confirm (bucket has no object versioning, so no
  historical generation to inspect) whether a stale `vm/setup-data-pipeline-vm.sh` GCS copy is the actual cause of the
  5/5 miss, but the absence of ANY freshness check across 139 launchers is a real, independently-confirmed gap
  regardless of whether it explains this specific incident.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags: [vm-launcher-runbook, spot-preemption, setup-script-freshness, gcs-staleness, fleet-wide]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/issues/vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md,
    /plans/active/issues/session_bound_vm_monitoring_reliability_gap_2026_07_26.md,
    /plans/archive/issues/vm_tarball_upload_expired_wif_token_interactive_slot_2026_07_25.md,
  ]
created: 2026-07-31
last_updated: 2026-07-31
priority: P2
parent_epic: infrastructure_master
source: "Found while working infra_satellite_ao_dispatch_batch1-007 (slot 8, backend_engineer, 2026-07-31)"
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: infra
drift_direction: advance-code
locked_since:
depends_on: []
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/infra_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/issues/vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md,
    /plans/active/issues/session_bound_vm_monitoring_reliability_gap_2026_07_26.md,
    /plans/epics/infrastructure_master.md,
  ]
---

# 139 VM launchers bypass the setup-script freshness guard

## What I found

Working `infra_satellite_ao_dispatch_batch1-007` ("Make the launcher's two best-effort GCS writes reliable"), I
live-swept every `af-backfill-*` VM log dir in `gs://deployment-scripts-central-element-323112/vm-logs/` (50 total,
2026-07-17..2026-07-31) and cross- referenced against
`gcloud compute operations list --filter="operationType=compute.instances.preempted AND targetLink~'af-backfill'"`,
which returned exactly 5 confirmed preemption events: `af-backfill-20260726-013313`, `-103202`, `-20260727-011039`,
`-055450`, `-20260731-123439`. **All 5 have NO `PREEMPTED` marker** in their `vm-logs/` dir — a 100% miss rate on
confirmed preemptions, not a rare one-off.

This is surprising because `setup-data-pipeline-vm.sh` (every one of these VMs' `startup-script-url`) already installs a
dedicated `uts-preemption-signal.service` systemd unit (`scripts/vm/setup-data-pipeline-vm.sh:117-208`) specifically to
write this marker fleet-wide, with its own 2-attempt retry and a 25s `TimeoutStopSec` budget (dated 2026-07-20/21 in its
own comments — i.e. already hardened, and that hardening should have been live for all 5 sampled failures). Two working
theories, not yet distinguished:

1. **The GCS copy of `setup-data-pipeline-vm.sh` was stale** at these VMs' boot time (missing the systemd-unit section
   entirely, or an earlier/less-hardened version of it). Could not confirm: the
   `deployment-scripts-central-element-323112` bucket has no object versioning enabled and the object has only ONE
   generation on record, so there is no historical copy to inspect against the preemption dates.
2. **The systemd unit runs but still loses the race in practice** (aggregate 3 metadata curls + up to 2
   `gcloud storage cp` attempts can exceed 25s on a loaded/small VM, since `gcloud storage cp` itself has a real
   Python-interpreter cold-start cost that isn't accounted for in the unit's own budget comment).

Regardless of which (both may be true), a real, independently-confirmed structural gap exists:
`lc_verify_setup_script_freshness` (`scripts/vm/lib/launcher_common.sh:878+`) — the function that would catch theory 1
by comparing the local repo's `setup-data-pipeline-vm.sh` against the GCS copy's md5 and warn/enforce/auto-republish —
is only invoked automatically inside `lc_gcloud_create` (`launcher_common.sh:293`). Measured directly:

```
$ grep -l "lc_gcloud_create" scripts/vm/*.sh | wc -l
4
$ grep -l "gcloud compute instances create" scripts/vm/*.sh | wc -l
139
```

**139 of 143 launcher scripts call `gcloud compute instances create` directly and never invoke
`lc_verify_setup_script_freshness` at all** (grep-confirmed — none of the 139 call it directly either).
`launcher_common.sh:291-292`'s own comment — _"checked here, not per-launcher, so every caller of lc_gcloud_create (~80
launchers) inherits it automatically"_ — is itself stale/inaccurate: the real count of `lc_gcloud_create` callers is 4,
not ~80. This means the overwhelming majority of the fleet has **zero automated warning** if
`vm/setup-data-pipeline-vm.sh` (or any other GCS-fetched startup script) on GCS drifts from the repo — a VM silently
boots against stale startup logic with no signal, the exact failure mode `lc_verify_tarball_freshness` (a sibling guard,
already called by most launchers for code tarballs) was built to prevent for tarballs specifically.

## Why it matters

`setup-data-pipeline-vm.sh` is the shared startup-script seam for the majority of the SPOT fleet — it is where the
fleet-wide preemption-signal unit, the file-descriptor limit, Python/uv install, and (per its own comments) "every
future launcher" preemption-recovery guarantee live. If this ONE file can drift silently on GCS with no automated check
across 139 launchers, every guarantee documented as "fleet-wide because it lives in the shared seam" is only as reliable
as someone remembering to manually re-run `create-code-tarballs.sh` (or whatever uploads `vm/*.sh`) after every relevant
deployment-service commit — exactly the kind of best-effort, unenforced assumption this same workspace's tarball-pinning
system was built to eliminate for code tarballs. This directly bears on the confirmed 5/5 af-backfill marker-miss
finding above (RESOLVED for af-backfill specifically this session by making its own inline shutdown- script
self-contained and baked-in — see infra_satellite_ao_dispatch_batch1_2026_07_26.md's todo — but the other 138 raw-create
launchers remain unguarded either way).

## Recommended decision

This is bigger than a single bounded todo — it is a fleet-wide audit + remediation across up to 139 files, and the
remediation shape itself needs a decision (migrate callers to `lc_gcloud_create`, vs. add a standalone
`lc_verify_setup_script_freshness` call to each raw-create launcher, vs. accept the mechanism-level fix — my af-backfill
launcher's own inline shutdown-script no longer depends on the GCS copy of `setup-data-pipeline-vm.sh` being fresh at
all — as the actual pattern to propagate). Filing as a scoped audit + a design question, not attempting the 139-file
sweep here.

- [x] ✅ [INFRA] P2. Correct `launcher_common.sh:291-292`'s stale "~80 launchers" comment to the measured count (4) — a
      one-line doc fix, cheap and immediately actionable. (repo: deployment-service) — deployment-service@daf3ad5
- [ ] [DATA] P2. Determine whether GCS object versioning can be retroactively enabled on
      `deployment-scripts-central-element-323112` (and the other `deployment-scripts-*` buckets) so a future incident of
      this shape has a historical generation to inspect — would have let this session confirm/refute theory 1 directly
      instead of leaving it open. (repo: deployment-service / infra — GCS bucket config, read the current bucket policy
      first)
- [ ] [OPERATOR] P2. Decide the remediation shape for the 139-launcher gap: (a) migrate high-value raw-create launchers
      to `lc_gcloud_create` (larger diff per launcher, but centralizes ALL pre-launch guards, not just this one); (b)
      add a standalone `lc_verify_setup_script_freshness` call to each raw-create launcher (smaller per-file diff, keeps
      the existing call shape); or (c) treat this session's af-backfill fix (make the launcher's own preemption
      mechanism self-contained, independent of the shared seam's freshness) as the real pattern to propagate instead,
      and only backfill the freshness-check for launchers that cannot be made self-contained. This is a design/
      architecture call, not a worker-determinable fact — do not dispatch a 139-file sweep speculatively without this
      decision. **Done when**: the operator names the chosen shape, then the follow-up remediation todo(s) can be scoped
      and drafted (likely its own dedicated plan, per the "too-large-for-a-batch-todo" precedent this same corpus
      already uses for other 100+-file sweeps).

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
