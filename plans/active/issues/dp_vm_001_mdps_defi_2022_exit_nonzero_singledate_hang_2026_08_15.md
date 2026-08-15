---
doc_type: issue
title:
  DP-VM-001 exit_code=1 on mdps-defi-2022-20260815-040118 — root cause is a single-date (2022-12-13) subprocess
  hang/timeout, non-OOM so page not relaunch
summary: >-
  A data-pipeline fleet monitor (exit-code-aware,
  `deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py`) detected VM `mdps-defi-2022-20260815-040118`
  terminated with a durable non-zero `exit_code=1` (not 137/OOM). This worker pulled `run.log` (via
  `_gcs.read_terminal_exit_code`/`read_text`, SDK, no subprocess) and found the actual root cause: of the 61 dates in
  the 2022-11-01..2022-12-31 incremental re-processing window, 60 completed cleanly (rc=0, most with 0 new candles since
  already current); exactly one, `date=2022-12-13`, hung and was killed by the per-date subprocess's own 1800s external
  timeout (`ERROR subprocess-per-date: date=2022-12-13 TIMED OUT after 1800s (FAILED, child killed)`), which is what
  flipped the overall handler's exit code to 1. Per DP-VM-001's own routing table
  (`/codex/05-infrastructure/data-pipeline-alerts.md`: "OOM: auto-recover (resize-up relaunch) then file issue ·
  non-OOM: page"), a non-OOM nonzero exit is a PAGE case, independent of any relaunch-count bound — same conclusion as
  the two 2026-08-14 precedent docs for this exact DP-VM-001 shape (mdps-cefi-2019, mdps-tradfi-2026), but this worker
  went one step further and actually diagnosed the in-container root cause via the GCS SDK reads those precedents
  explicitly deferred. Also found: 4 separate mdps-defi-2022-* VMs are already running (launched 07:21-08:15Z today),
  each targeting a DIFFERENT single missing/stalled date (2022-12-24, 2022-11-16, 2022-11-11, 2022-11-07 respectively,
  via `--no-subprocess-per-date --start-date X --end-date X`) — consistent with an existing automated per-date gap-fill
  actuator (heartbeat_stall_watcher.py pattern) already converging on defi/2022 gaps, but `2022-12-13` specifically is
  NOT among the 4 in-flight retries. This worker did NOT relaunch the year-shard VM (would duplicate/race the
  already-running per-date gap-fill fleet and violate DP-VM-001's non-OOM=page routing) and did NOT attempt a code fix
  for the underlying per-date hang (out of one-shot escalation scope — no traceback/stack for the hang itself was found
  in `run.log`, only the external 1800s-timeout kill marker) — it files this doc and pages the operator.
status: open
nature: issue
asset_group: [defi]
stage: [meta]
repos: [deployment-service, market-data-processing-service]
scope: [engineer, admin]
tags: [dp-vm-001, exit-code-monitor, mdps-defi, single-date-hang, page, data-pipeline-monitors]
related:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/issues/dp_vm_001_mdps_cefi_2019_exit_nonzero_relaunch_bound_page_2026_08_14.md,
    /plans/active/issues/dp_vm_001_mdps_tradfi_2026_exit_nonzero_relaunch_bound_page_2026_08_14.md,
    /plans/active/issues/dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14.md,
  ]
context_scope:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py,
    deployment-service/deployment_service/data_pipeline_monitors/_gcs.py,
    deployment-service/deployment_service/data_pipeline_monitors/heartbeat_stall_watcher.py,
    deployment-service/scripts/vm/launch-mdps-sharded-backfill.sh,
  ]
created: "2026-08-15"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: devops
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Escalation agt-849fd6 (wall_type=data_pipeline_failure, dispatched to slot 3, 2026-08-15) — client_payload carried
  vm_name=mdps-defi-2022-20260815-040118, asset_group=defi, no separate audit CSV attached ("Filed issue: (none — alert
  carries the details)"). VM confirmed absent from the live fleet this session (`gcloud compute instances list
  --filter="name~mdps-defi-2022-20260815-040118"` returned zero rows, ~08:26Z) — consistent with a
  terminated/self-deleted VM. `run.log` pulled via
  `deployment_service.data_pipeline_monitors._gcs.read_text`/`read_terminal_exit_code` against
  `gs://deployment-scripts-central-element-323112/` (SDK, never subprocess `gsutil`/`gcloud storage`).
---

# DP-VM-001 — mdps-defi-2022-20260815-040118 exit_code=1, single-date hang, page not relaunch

## What happened

- VM: `mdps-defi-2022-20260815-040118` (asset_group=defi, year-shard=2022, launcher-family prefix `mdps-defi-`),
  launched ~04:01Z per its name, part of the `launch-mdps-sharded-backfill.sh` DeFi 2022-2026 fan-out (one VM per
  asset_group × year shard).
- Task: incremental re-processing of `defi/2022-11-01..2022-12-31` (61 dates), 7 timeframe shards each.
- Terminal state (per `EXIT_STATUS`/`run.log` `rc=` markers, read via the SDK): `exit_code=1`.
- `run.log` evidence (tail + full-text grep, 4160 lines / 542168 bytes):
  - 60/61 dates in the window completed cleanly, most with `subprocess-per-date: date=<d> rc=0 (ok)` and 0 new candles
    (already current from a prior run — genuinely nothing to do).
  - The lone exception:
    `2026-08-15 05:33:33,300 ERROR subprocess-per-date: date=2022-12-13 TIMED OUT after 1800s (FAILED, child killed)` —
    this date's per-date subprocess hung until the external 1800s watchdog killed it. No traceback/exception was
    captured for the hang itself (the kill is an external SIGTERM/SIGKILL against a subprocess that never logged its own
    failure) — the in-process root cause of the hang (which of the 7 timeframe shards / which GCS or upstream call for
    `2022-12-13` blocked) is NOT determinable from `run.log` alone.
  - `2026-08-15 05:56:48,488 ERROR Handler returned non-zero exit code: 1` — the overall year-shard handler surfaces ANY
    per-date failure as its own exit code, so one hung date flipped an otherwise-61/61-clean run to `exit_code=1`.
- Live-fleet cross-check (~08:26Z, ~2.5h after the failed VM's start): 4 separate `mdps-defi-2022-*` VMs are RUNNING
  (`20260815-072104`, `-080135`, `-080853`, `-081538`), each launched with a **single specific date** via
  `--no-subprocess-per-date --start-date <d> --end-date <d>` — respectively `2022-12-24`, `2022-11-16`, `2022-11-11`,
  `2022-11-07`. This is a different launch shape than the year-shard VM (which processes the whole incremental-missing
  range per invocation) and matches an automated per-date gap-fill pattern (the `heartbeat_stall_watcher.py` module
  carries this same `no-subprocess-per-date` single-date retry shape). **None of the 4 in-flight retries targets
  `2022-12-13`** — the date that actually caused this VM's failure.

## Why this is a PAGE case, not a relaunch

`/codex/05-infrastructure/data-pipeline-alerts.md` DP-VM-001 routing: **"OOM: auto-recover (resize-up relaunch) then
file issue · non-OOM: page."** `exit_code=1` is not 137 — not eligible for blind auto-recover regardless of any
relaunch-count bound, mirroring the two DP-VM-001 precedents filed 2026-08-14 for `mdps-cefi-2019` and
`mdps-tradfi-2026`. Additionally, `RB-INFRA-RELAUNCH` step 3 says to stand down when an actively-cycling
wrapper/actuator is already converging on the same shard — the 4 in-flight single-date retry VMs are exactly that signal
for the DeFi 2022 shard's OTHER stalled dates, so a manual full-year-shard relaunch right now would race that in-flight
fleet (and violate the sharded-backfill launcher's one-VM-per-(asset_group,year) design) without even fixing the one
date (`2022-12-13`) that actually needs it.

## What this worker did NOT do

- Did not relaunch the `mdps-defi-2022` year-shard VM, or launch a targeted single-date VM for `2022-12-13` (that is the
  operator's/BACKEND's call per the recommended decision below — launching a 5th concurrent `mdps-defi-2022-*` VM
  without confirming the gap-fill actuator's own queue/bound first risks duplicating or racing it).
- Did not diagnose WHY `2022-12-13`'s subprocess hung for 1800s (no exception/traceback exists in `run.log` for the hang
  itself, only the external timeout-kill marker) — that requires either a live repro of that specific date or
  instrumenting the per-date subprocess with finer-grained internal timeouts (the actual code-level fix, per the
  workspace's "bound unbounded calls" pattern for DP-VM-003/004-class stalls, would apply here too even though this
  fired as DP-VM-001).

## Recommended decision (for the operator)

1. **[WORKER REC] Wait for the automated per-date gap-fill actuator to reach `2022-12-13`** (it is already actively
   working through other defi/2022 gaps 07:21-08:15Z) rather than manually launching a competing VM right now; re-check
   the live fleet + manifest for `defi/2022-12-13` coverage in a follow-up sweep.
2. Alternative: manually launch a single-date `mdps-defi-2022` retry VM scoped to `2022-12-13` only
   (`--no-subprocess-per-date --start-date 2022-12-13 --end-date 2022-12-13`), if the operator wants it resolved
   immediately rather than waiting on the actuator's own cadence.
3. Separately, file/prioritize the code-level follow-up: give the per-date MDPS candle-derivation subprocess its own
   internal `asyncio.wait_for(..., timeout=N)` bound around whichever upstream call is likely to hang (GCS list/read or
   an external dependency check), so a genuine stall fails fast with a real exception/traceback instead of silently
   consuming the full 1800s external watchdog budget with no diagnostic signal.

## Todos

- [ ] [OPERATOR] P1. Decide relaunch-vs-wait for `defi/2022-12-13` MDPS candle coverage per the recommended decision
      above.
- [ ] [BACKEND] P2. Once `run.log` is reproducible for a `2022-12-13`-shaped hang (or a similar future DP-VM-001 single
      -date hang), add an internal per-shard timeout bound around the blocking call inside the MDPS per-date subprocess
      so it raises a diagnosable exception instead of relying solely on the external 1800s kill.

## Progress Log

- 2026-08-15 (slot 3, data_pipeline_failure escalation agt-849fd6): Received escalation for DP-VM-001
  `mdps-defi-2022-20260815-040118` exit_code=1. Confirmed via `gcloud compute instances list` the VM is no longer in the
  live fleet (0 rows). Pulled `run.log` (542168 bytes, 4160 lines) via the SDK helpers
  (`_gcs.read_terminal_exit_code`/`read_text`) and grepped it for ERROR/Traceback/nonzero-rc markers: found exactly one
  failure signature — `date=2022-12-13 TIMED OUT after 1800s (FAILED, child killed)` — against 60/61 otherwise clean
  dates. Cross-checked the live fleet and found 4 concurrent `mdps-defi-2022-*` VMs already running single-date retries
  for OTHER dates (not `2022-12-13`), consistent with an existing automated gap-fill actuator already converging. Per
  DP-VM-001's routing table (non-OOM → page) and RB-INFRA-RELAUNCH's stand-down guidance (don't race an
  already-converging actuator), did NOT relaunch. Filed this issue doc with the diagnosed root cause (a step beyond the
  two 2026-08-14 precedent docs, which explicitly deferred `run.log` reading) and paged the operator via `/blocked`.
