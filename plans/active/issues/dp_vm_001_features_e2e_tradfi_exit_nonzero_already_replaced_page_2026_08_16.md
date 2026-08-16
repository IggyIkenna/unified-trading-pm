---
doc_type: issue
title:
  DP-VM-001 exit_code=1 on features-e2e-tradfi-20260816-015304-1efb38 — non-OOM exit routes to page per DP-VM-001's own
  routing table; a fresh replacement VM (same argv hash) is already RUNNING, so no relaunch is needed either way
summary: >-
  A data-pipeline fleet monitor (exit-code-aware, `deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py`)
  detected VM `features-e2e-tradfi-20260816-015304-1efb38` (a `/data-pipeline-check-features` E2E smoke-check shard VM,
  launched by `features-service/scripts/pipeline_e2e_check.py` via `launch-features-vm.sh --vm-name-override`, NOT a
  genuine backfill VM) terminated with a durable non-zero `exit_code=1` (not 137/OOM). This worker's dispatch context
  carried a generic "RELAUNCH" instruction, but per DP-VM-001's own routing table
  (`/codex/05-infrastructure/data-pipeline-alerts.md` line 138: "OOM: auto-recover (resize-up relaunch) then file issue
  · non-OOM: page"), a non-OOM nonzero exit is UNCONDITIONALLY a page case — verified directly against the codex SSOT
  this session (mirrors the same-day precedent
  `dp_vm_001_mdps_tradfi_2025_exit_nonzero_page_2026_08_16.md`), independent of the relaunch-bound question. Also
  confirmed via `gcloud compute instances list --filter="name~'^features-e2e-'"` that a FRESH replacement VM,
  `features-e2e-tradfi-20260816-030150-1efb38` — same argv hash suffix `1efb38` (deterministic per-shard hash), later
  `RUN_TS` — is currently RUNNING: the e2e-check driver (or its scheduling cron) already re-ran this exact shard, so a
  manual relaunch here would also have raced/duplicated a live run even setting the routing question aside. This worker
  did NOT relaunch.
status: open
nature: issue
asset_group: [tradfi]
stage: [meta]
repos: [deployment-service, features-service]
scope: [engineer, admin]
tags: [dp-vm-001, exit-code-monitor, features-e2e, pipeline-e2e-check, page, data-pipeline-monitors]
related:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/issues/dp_vm_001_mdps_tradfi_2025_exit_nonzero_page_2026_08_16.md,
  ]
context_scope:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py,
    deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py,
    features-service/scripts/pipeline_e2e_check.py,
  ]
created: "2026-08-16"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.2
assigned_role: devops
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Escalation agt-4bafe0 (wall_type=data_pipeline_failure, dispatched to slot 4, 2026-08-16). Boot context named the
  finding + a "RELAUNCH" instruction directly ("Filed issue: (none — alert carries the details)"). This worker
  independently verified against `/codex/05-infrastructure/data-pipeline-alerts.md`'s DP-VM-001 routing table that a
  non-OOM `exit_code=1` routes to page, not relaunch, and additionally confirmed a fresh same-shard replacement VM is
  already RUNNING before considering the relaunch path.
---

# DP-VM-001 — features-e2e-tradfi-20260816-015304-1efb38 exit_code=1, non-OOM, page not relaunch (replacement already running)

## What happened

- VM: `features-e2e-tradfi-20260816-015304-1efb38` — **not a backfill VM**: `launcher_registry.py`'s generic
  `"features-": "launch-features-vm.sh"` prefix would resolve a launcher for it, but the VM name itself is minted by
  `features-service/scripts/pipeline_e2e_check.py` (the `/data-pipeline-check-features` E2E smoke-check driver) via
  `launch-features-vm.sh`'s `--vm-name` override hook (comment at `scripts/vm/launch-features-vm.sh:255`: "pipeline-e2e-check
  driver supplies a deterministic name"). Confirmed the naming convention from a prior in-code example
  (`_FAMILY_TIMEOUT_OVERRIDES` docstring in `pipeline_e2e_check.py`: `features-e2e-cefi-20260730-133536-025349`) —
  `features-e2e-{asset_group}-{RUN_TS}-{argv_hash}`. Output is TEST-BUCKET-ONLY (force/skip legs never touch PROD), so
  this finding is a smoke-check shard failure, not a data-pipeline capture gap.
- Terminal state: `exit_code=1` (non-zero, non-OOM).
- This worker's dispatch context said "RELAUNCH vm=features-e2e-tradfi-20260816-015304-1efb38 launcher=(resolve via
  launcher_registry) ... asset_group=tradfi" — generic dispatch boilerplate, not gated on the OOM-vs-non-OOM
  distinction. Read `/codex/05-infrastructure/data-pipeline-alerts.md` line 138 directly this session: "OOM:
  auto-recover (resize-up relaunch) then file issue · non-OOM: page" — unconditional on exit code class. `exit_code=1`
  is non-OOM (OOM is 137). Routing = **page**. Same conclusion, independently reached, as the same-day sibling doc
  `dp_vm_001_mdps_tradfi_2025_exit_nonzero_page_2026_08_16.md` (different VM family — mdps-tradfi vs features-e2e —
  same DP-VM-001 routing-table logic).
- Cross-checked against `scripts/recovery/relaunch_backfill_vm.py`'s own contract (the actuator `escalation.py` wires
  for `DP_VM_EXIT_NONZERO`): "Only `exit_code == 137` (OOM) is relaunched here; any other non-zero exit returns a
  `status=SKIPPED` (not_oom) so the page-tier owns it." Code and codex doc agree.
- **Additionally confirmed via `gcloud compute instances list --filter="name~'^features-e2e-'"`** that a fresh
  replacement VM, `features-e2e-tradfi-20260816-030150-1efb38`, is currently `RUNNING` (created
  `2026-08-15T20:04:24-07:00`, i.e. `RUN_TS=20260816-030150` — later than the failed VM's `RUN_TS=20260816-015304`) —
  **same argv-hash suffix `1efb38`**, meaning it is the SAME shard config re-run. Per RB-INFRA-RELAUNCH's own guidance
  ("check the live VM fleet for an ALREADY-RUNNING replacement... a later automated sweep may have already relaunched
  successfully under a fresh timestamped VM name"), this confirms the e2e-check driver (or its scheduling cron)
  already re-ran this exact shard — a manual relaunch here would have duplicated a live run, independent of the
  routing-table question above.
- No prior issue doc named this specific VM (grepped `plans/active/issues/` for
  `features-e2e-tradfi-20260816-015304-1efb38` and `features_e2e_tradfi` — zero hits before this doc).
- Did NOT pull `run.log`/`EXIT_STATUS`/`LAUNCH_PARAMS.json` content to diagnose the in-container root cause (which
  feature-family/leg failed and why) — deferred, same scoping as the `mdps_tradfi_2025` sibling doc; a genuine
  root-cause pass is follow-up work, and since a replacement is already running the operational urgency is lower.

## Per DP-VM-001's own routing table (`data-pipeline-alerts.md` line 138)

> "OOM: auto-recover (resize-up relaunch) then file issue · non-OOM: page"

`exit_code=1` is non-OOM (not 137). Routing = **page**. A replacement is already running, so no relaunch action is
needed regardless.

## What this worker did NOT do (scope of this session)

- Did NOT relaunch `features-e2e-tradfi-20260816-015304-1efb38` (non-OOM exit routes to page per DP-VM-001's own
  table; a same-hash replacement is already RUNNING, so a relaunch would have duplicated it anyway).
- Did NOT pull `run.log`/`LAUNCH_PARAMS.json`/`EXIT_STATUS` to diagnose the in-shard root cause (which feature-family
  × leg failed, e.g. `delta_one`/`volatility`/`cross_instrument` force vs skip vs canonical) — follow-up work.

## Recommended decision

A: Operator (or a devops-role worker) pulls `run.log` for `features-e2e-tradfi-20260816-015304-1efb38`
(`gs://deployment-scripts-<project>/vm-logs/features-e2e-tradfi-20260816-015304-1efb38/run.log`, read via UTL's
`get_storage_client`, never a subprocess `gsutil`), diagnoses the `exit_code=1` root cause (which shard/leg), and
either fixes the underlying `features-service`/`pipeline_e2e_check.py` bug the smoke check surfaced, or confirms it
was a transient infra blip now resolved by the already-running replacement (`features-e2e-tradfi-20260816-030150-1efb38`).

B: Treat as superseded by the already-running replacement VM; no further action needed unless the replacement also
fails.

**Recommendation: B** — a same-shard replacement is already running (unlike the `mdps-tradfi` sibling doc, where no
replacement was found), so the operational risk here is low; A is worth doing only if the replacement also fails or
this recurs.

## Progress Log

- 2026-08-16: Filed by slot-4 `data_pipeline_failure` escalation worker (escalation `agt-4bafe0`). Verified DP-VM-001's
  routing table directly against the codex SSOT (non-OOM → page, unconditional) and against
  `relaunch_backfill_vm.py`'s own actuator contract (exit_code!=137 → SKIPPED/not_oom → page tier). Confirmed the VM is
  a `pipeline_e2e_check.py` E2E smoke-check shard (test-bucket-only), not a genuine backfill VM. Confirmed via
  `gcloud compute instances list` that a fresh same-hash replacement (`features-e2e-tradfi-20260816-030150-1efb38`) is
  already RUNNING. Did not relaunch. Did not pull `run.log` (deferred). Paging the operator now via `/api/slots/4/blocked`.
