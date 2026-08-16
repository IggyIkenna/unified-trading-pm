---
doc_type: issue
title:
  DP-VM-001 exit_code=1 on mdps-tradfi-2023-20260815-040118 — mdps-tradfi- launcher family already at the 2/(prefix,day)
  relaunch bound, page instead of relaunch
summary: >-
  A data-pipeline fleet monitor (exit-code-aware,
  `deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py`) detected VM `mdps-tradfi-2023-20260815-040118`
  terminated with a durable non-zero `exit_code=1` (not 137/OOM) — the capture did not complete cleanly. Per DP-VM-001's
  own routing table (`/codex/05-infrastructure/data-pipeline-alerts.md`: "OOM: auto-recover (resize-up relaunch) then
  file issue · non-OOM: page"), a non-OOM nonzero exit is a PAGE case, not an auto-recover case, independent of any
  relaunch-count bound. The dispatching escalation additionally reported the `mdps-tradfi-` launcher-family had already
  hit the `≤2/(vm-prefix, day)` relaunch bound (RB-INFRA-RELAUNCH) earlier today (2026-08-15), reinforcing that a
  further relaunch here would be a further blind retry, not new information. A grep of `plans/active/issues/` found no
  prior doc naming this specific VM. Two prior `mdps-tradfi-` relaunch-bound-page docs exist from 2026-08-14
  (`dp_vm_001_mdps_tradfi_2026_exit_nonzero_relaunch_bound_page_2026_08_14.md`) and 2026-08-15
  (`dp_vm_001_tradfi_bf_cme_ohlcv_1m_es_2020_exit137_stall_relaunch_bound_page_2026_08_15.md`) — same failure class
  recurring against the `mdps-tradfi-`/`tradfi-bf-` launcher families, worth a cross-check for a shared root cause in
  the tradfi backfill launcher rather than treating each VM as an isolated incident. This worker did NOT relaunch
  (per the dispatching escalation's explicit instruction — the family was already at its relaunch bound) and did NOT
  pull `run.log` content to diagnose the in-container root cause this session (see Progress Log); it files this doc and
  attempts to page the operator per the escalation's instruction. The orchestrator HTTP surface
  (`http://localhost:8765`) was unreachable from this session for the entire task (heartbeat/progress/blocked/done all
  connection-refused) — see Progress Log; this doc is the durable page in place of the `/blocked` call.
status: open
nature: issue
asset_group: [tradfi]
stage: [meta]
repos: [deployment-service, market-data-processing-service]
scope: [engineer, admin]
tags: [dp-vm-001, exit-code-monitor, mdps-tradfi, relaunch-bound, page, data-pipeline-monitors]
related:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/issues/dp_vm_001_mdps_tradfi_2026_exit_nonzero_relaunch_bound_page_2026_08_14.md,
    /plans/active/issues/dp_vm_001_mdps_cefi_2019_exit_nonzero_relaunch_bound_page_2026_08_14.md,
    /plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_es_2020_exit137_stall_relaunch_bound_page_2026_08_15.md,
    /plans/active/issues/mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
context_scope:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py,
    deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py,
  ]
created: "2026-08-15"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
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
  Escalation agt-5801ea (wall_type=data_pipeline_failure, dispatched to slot 10, 2026-08-15). Boot context carried the
  finding directly — no separate audit CSV/candidate list was attached ("Filed issue: (none — alert carries the
  details)"). Boot context explicitly instructed: do NOT relaunch `mdps-tradfi-2023-20260815-040118` (launcher family
  `mdps-tradfi-` already at 2/2 relaunch dispatches today), check for an existing open issue doc, and page the operator
  instead of relaunching again. VM confirmed absent from the live fleet this session
  (`gcloud compute instances list --filter="name~mdps-tradfi-2023"` returned zero rows) — consistent with a
  terminated/self-deleted VM, not evidence of anything further.
---

# DP-VM-001 — mdps-tradfi-2023-20260815-040118 exit_code=1, relaunch-bound, page not relaunch

## What happened

- VM: `mdps-tradfi-2023-20260815-040118` (asset_group=tradfi, year-shard=2023, launcher-family prefix `mdps-tradfi-` →
  `launch-mdps-sharded-backfill.sh` per `launcher_registry.py`).
- Terminal state: `exit_code=1` (non-zero, non-OOM) — captured did not complete cleanly.
- The `mdps-tradfi-` launcher family had already used its `≤2/(vm-prefix, day)` relaunch allowance today
  (2026-08-15) per the dispatching escalation's context — a third relaunch would be a blind retry, not new information.
- No prior issue doc named this specific VM (grepped `plans/active/issues/` for `mdps-tradfi-2023` and
  `mdps_tradfi_2023` — zero hits before this doc).
- **Possible shared-root-cause signal**: this is the THIRD `mdps-tradfi-`/`tradfi-bf-` relaunch-bound-page doc in two
  days (2026-08-14, 2026-08-14, 2026-08-15 — see `related:`). Worth a follow-up audit of the tradfi MDPS backfill
  launcher/adapter path for a systemic non-OOM failure mode rather than treating each occurrence as isolated. Not
  diagnosed in this session — flagged for the operator / a future devops-tagged todo.

## Per DP-VM-001's own routing table (`data-pipeline-alerts.md`)

> "OOM: auto-recover (resize-up relaunch) then file issue · non-OOM: page"

`exit_code=1` is non-OOM (not 137). Routing = **page**, independent of the relaunch-bound question — the relaunch-bound
context from the escalation is corroborating, not the primary reason to page.

## What this worker did NOT do (scope of this session)

- Did NOT relaunch `mdps-tradfi-2023-20260815-040118` (per explicit dispatch instruction + the confirmed relaunch bound).
- Did NOT pull `run.log` / `LAUNCH_PARAMS.json` / `PROGRESS.json` content to diagnose the in-container root cause — a
  deeper root-cause pass (why `exit_code=1`, which shard/date range, timeout vs adapter error vs schema issue) is
  follow-up work for whoever picks this doc up.
- Confirmed via `gcloud compute instances list --filter="name~mdps-tradfi-2023"` that the VM is no longer present in the
  live fleet (zero rows) — consistent with a terminated/self-deleted VM.

## Orchestrator HTTP surface unreachable this session

`http://localhost:8765` (the orchestrator server this worker's boot message names as `$SERVER_URL`) refused every
connection attempted this session (`heartbeat`, and every subsequent progress/blocked/done call would hit the same
failure) — `curl: (7) Failed to connect to localhost port 8765`. This worker could not post a `/blocked` question or a
`/progress` heartbeat through the normal channel. This issue doc is filed as the durable page artifact in place of the
`/blocked` call the role brief calls for; the operator should also check orchestrator-VM health independently, since an
unreachable `:8765` from a slot session is itself worth a look (possibly `/check-agent-orchestrator` or a direct
service-restart-procedure check), though diagnosing that is out of scope for this data-pipeline-focused escalation.

## Recommended decision

A: Operator (or a future devops-role worker) pulls `run.log` for `mdps-tradfi-2023-20260815-040118` from its GCS log
path, diagnoses the `exit_code=1` root cause, and either fixes it before the next scheduled tradfi-2023 backfill attempt
or files a targeted follow-up. Given the THIRD same-shape page in two days, also worth cross-checking the
`mdps-tradfi-`/`tradfi-bf-` launcher/adapter code path for a systemic bug (recommended — B is fallback only).

B: Treat as an isolated one-off VM failure, let the next scheduled relaunch (tomorrow, fresh relaunch-bound budget) try
again with no further diagnosis.

**Recommendation: A** — three same-shape non-OOM tradfi pages in 48h is a pattern, not noise; a root-cause pass on the
launcher/adapter is cheaper than repeatedly burning the daily relaunch bound on VMs that keep exiting the same way.

## Progress Log

- 2026-08-15: Filed by slot-10 data_pipeline_failure escalation worker (escalation agt-5801ea). Confirmed VM absent
  from live fleet. Confirmed no prior issue doc for this VM. Did not relaunch (per dispatch instruction + confirmed
  relaunch bound). Did not diagnose in-container root cause (no `run.log` pull this session). Orchestrator HTTP surface
  (`:8765`) was unreachable for the entire session — heartbeat/progress/blocked/done calls all connection-refused; this
  doc stands in place of the `/blocked` page.
- 2026-08-15 (slot 12, same escalation `agt-5801ea` — apparently dispatched to two slots for the same finding):
  Independently wrote a duplicate doc at this same path, then on push hit a rebase-autostash conflict against this
  already-landed slot-10 version. Confirmed both docs reached the identical conclusion (non-OOM `exit_code=1` →
  page, do not relaunch; no code change) — resolved by keeping this landed version intact (added one purely-additive
  `related:` link to `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md`) per the "append, don't overwrite
  landed content" rule, rather than replacing it with the duplicate. Orchestrator `:8765` was also unreachable from
  slot 12 this session, consistent with slot 10's report — this is the paging artifact for both dispatches.
- **context-scout 2026-08-16**: re-scouted; context_scope re-verified (4 entries), unchanged.
