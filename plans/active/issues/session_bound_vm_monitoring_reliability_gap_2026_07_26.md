---
doc_type: issue
title:
  Session-bound Claude Code monitoring (ScheduleWakeup loops) for ad hoc backfill VMs inherits the operator's own
  connectivity/session-continuity dependency — a real, measured blind spot, not just the already-documented "one-off VMs
  aren't wired into the fleet monitor" gap
summary: >-
  While monitoring a FIXTURES backfill VM (af-backfill-20260726-013313) via a self-armed ScheduleWakeup loop
  (/autonomous, operator away ~6h), the VM was genuinely SPOT-preempted at 2026-07-26T04:16:47Z (confirmed via `gcloud
  compute operations list` — systemevent compute.instances.preempted) and went undetected for ~5h20m before the operator
  reconnected and asked "seems to have stopped." CLAUDE.md already documents that one-off/ad hoc VMs aren't wired into
  the fleet-level auto-relaunch watchdog ("this is on you, not automatic") — the gap found here is one level deeper: an
  agent's own self-armed session-bound monitoring loop (ScheduleWakeup ticks re-invoking the same Claude Code session)
  is NOT a substitute for that missing infrastructure watchdog, because it inherits the SAME dependency the operator has
  — if the session/client can't be reached (the operator's own reported connectivity drop, in this case), scheduled
  wakeups cannot fire or act, so the blind spot persists exactly as long as the connectivity gap does. Shortening the
  check interval does not close this gap (it only bounds the window when the session IS reachable); the only real fix is
  an out-of-band watchdog that does not depend on any particular Claude Code session staying connected.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, instruments-service]
scope: [engineer, admin]
tags: [vm-monitoring, spot-preemption, autonomous-agent, watchdog, reliability, session-bound]
related:
  [
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/active/infra_satellite_ao_dispatch_batch10_2026_08_09.md,
  ]
created: 2026-07-26
author: unknown
last_updated: 2026-08-09
priority: P2
parent_epic: infrastructure_master
source:
  "Measured during an interactive /autonomous session monitoring af-backfill-20260726-013313 (FIXTURES curated-universe
  backfill); operator reconnected after ~5h20m and reported the VM 'seems to have stopped', which led to discovering the
  preemption + the undetected gap via `gcloud compute operations list`."
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
drift_direction: advance-code
resolved_by:
locked_by:
context_scope:
  [
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    deployment-service/scripts/vm/lib/launcher_common.sh,
  ]
depends_on: []
---

# Session-bound monitoring loops for ad hoc VMs share the operator's connectivity blind spot

## Evidence (2026-07-26)

- VM `af-backfill-20260726-013313` (asia-northeast1-c) launched ~2026-07-26T00:36Z with a self-armed
  `ScheduleWakeup`-based monitoring loop (30min cadence, per `/autonomous` rules — the operator was away ~6h).
- `gcloud compute operations list --filter="targetLink~'af-backfill-20260726-013313'"` shows
  `systemevent-...-compute.instances.preempted` at `2026-07-25T21:16:47.177-07:00` = `2026-07-26T04:16:47Z`, matching
  exactly where `run.log` goes silent (last heartbeat `04:15:12Z`, no `DEPLOYMENT_FAILED`/exit-code trace, no
  `PREEMPTED` marker file — the shutdown grace period was too short for the shutdown-script to upload it).
- The VM was not detected as dead until the operator reconnected at ~09:30Z and reported "seems to have stopped" — a
  **~5h20m undetected gap**, despite a monitoring loop having been armed the whole time.
- No evidence the loop's `ScheduleWakeup` calls failed to be _scheduled_; the working theory (not proven, since there is
  no log of missed harness-level wakeups) is that the calls could not be _delivered/acted on_ while the operator's own
  session/client was unreachable, since `ScheduleWakeup` re-invokes the same interactive session.

## Why this is a distinct finding from the existing "one-off VMs aren't fleet-monitored" rule

CLAUDE.md (`Launching VMs / infra`) already says: _"Manually checking in on a SPOT VM that looks stalled/gone: verify
`compute.instances.preempted`... BEFORE diagnosing a bug/hang — one-off migration VMs aren't wired into the fleet
monitor, so this is on you, not automatic."_ That correctly assigns responsibility to **a** watcher. What's new here:
when the assigned watcher is an **agent's own session-bound loop** rather than a human periodically checking in, the
loop's uptime is bounded by the SAME session/connectivity continuity as the human it's substituting for — it is not an
independent, infrastructure-level guarantee. A human who steps away and a Claude Code session that goes unreachable fail
in the same way and at the same time when they're the same physical connection.

## Todos

- [x] ✅ [DATA] P2. **DECIDED 2026-08-08 — operator ruling (item 78, this doc's own Progress Log entry "2026-08-08
      (operator Q&A round5, infra tranche, item 78)" below,
      `session_bound_vm_monitoring_reliability_gap_2026_07_26.md`): (b) wire into the fleet-level `RelaunchPreemptedVm`
      / exit-code-fleet-monitor actuator**, not a documented-best-effort caveat. Scoping read of the actual current code
      (`deployment-service/deployment_service/data_pipeline_monitors/{cli.py,exit_code_fleet_monitor.py,     launcher_registry.py,vm_classification.py}`,
      `deployment-service/scripts/recovery/relaunch_backfill_vm.py`) confirms the fleet-level actuator is **already
      built and already NOT session-bound**: `cli.py --mode exit-code` runs on a Cloud Scheduler cadence
      (`dp_exit_code_monitor_cron`, `*/5 * * * *`), scans the WHOLE project's RUNNING VM census via
      `_list_running_vms()` (unfiltered `aggregated_list_instances`, not a session-armed watch), filters to data VMs via
      `vm_classification.is_data_vm()` (an asset_group-name substring OR a `DATA_VM_PREFIXES` entry), and for any
      terminated VM whose prefix has a `launcher_registry.LAUNCHER_FOR_VM_PREFIX` binding, a PREEMPTED verdict
      unconditionally fires `RelaunchPreemptedVm` via `escalation.py`'s `auto_recover` tier — independent of any Claude
      Code session staying reachable. So the 2026-07-26 `af-backfill-*` incident this issue is about was NOT a
      "session-bound monitoring is inherently unreliable" problem — it was `af-backfill-` being **absent from
      `vm_classification.DATA_VM_PREFIXES`** at the time (confirmed: `LAUNCHER_FOR_VM_PREFIX` already had it, but the
      census filter didn't), so the fleet sweep never even considered the VM. That specific gap was found + fixed
      2026-08-04 (`plans/archive/issues/af_backfill_preemption_auto_recovery_not_firing_2026_08_04.md`,
      `deployment-service@16938c1`), which also added a guard test
      (`test_data_vm_prefixes_cover_every_relaunchable_launcher`) so an existing `LAUNCHER_FOR_VM_PREFIX` entry can
      never again silently drop out of `DATA_VM_PREFIXES`. The residual gap — a **brand-new** one-off/ad hoc launcher
      script whose `VM_NAME=`/`VM_PREFIX=` was never registered in ANY of the three registries in the first place (which
      is exactly how `af-backfill-` went unnoticed for ~9 days before the 2026-08-04 fix, and would recur for the next
      novel one-off backfill VM naming scheme) — is filed as the scoped follow-up build below.

- [x] ✅ [SCRIPT] P2. **EXTRACTED 2026-08-09 → `infra_satellite_ao_dispatch_batch10_2026_08_09.md` todo 1 — SHIPPED
      `deployment-service@c8f1612b`.** Built the forward-registration CI guard
      (`check_vm_launcher_prefix_registration.py`) so a NEW ad hoc/one-off backfill launcher can never launch a VM
      invisible to the fleet monitor: derives each launcher's prefix, fails when uncovered by
      `is_data_vm()`/unregistered in `LAUNCHER_FOR_VM_PREFIX`, wired into `quality-gates.sh`, baseline-ratcheted (39
      pre-existing launchers grandfathered), `launcher_registry.py` docstring +
      `/codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md` updated with the closed-loop registration
      contract, 8 new unit tests (incl. a synthetic unregistered-launcher case) — all green. Reconciled by
      `infra_satellite_ao_dispatch_batch10_finalize_2026_08_09.md` todo 1.
- [ ] [DATA] P3. **Audit whether the `PREEMPTED` marker's shutdown-script grace period is survivable in practice** — the
      marker write (`gcloud storage cp` of a one-line file) didn't complete before this instance was reclaimed, which is
      the SAME mechanism `zombie_watchdog`/`exit_code_fleet_monitor` rely on to classify a gone VM as a benign
      preemption vs. an unexplained disappearance. If the write frequently loses the race, the marker is not a reliable
      signal fleet-wide, not just for this one VM. (repo: deployment-service `scripts/vm/lib/launcher_common.sh`'s
      shutdown-script template). **Done when**: either measured evidence the race is rare (this was a one-off), or a
      mitigation (e.g. writing the marker earlier / more defensively) is proposed.

## Progress Log

- **infra_satellite_ao_dispatch_batch10_finalize 2026-08-09 (slot 23, review)**: Reconciled the `[SCRIPT] P2`
  forward-registration CI guard todo — flipped to `[x]` citing `deployment-service@c8f1612b`
  (`infra_satellite_ao_dispatch_batch10_2026_08_09.md` todo 1, shipped 2026-08-09). Confirmed this doc is NOT an
  archival candidate: the `[DATA] P3` PREEMPTED-marker grace-period survivability audit remains open by design (a
  genuine undecided design choice, untouched by this batch's scope) — `grep -cE '^- \[ \]'` = 1 after this flip.
- **na-eligibility-audit 2026-08-09** (infra tranche) [body-hash:53c7ebb01b2b239b]: KEEP-NA-STALE (already-duplicated) —
  1 of 2 items. Todo 1 is already correctly self-annotated as EXTRACTED into
  `infra_satellite_ao_dispatch_batch10_2026_08_09.md` todo 1 (status: active, confirmed). Todo 2 (PREEMPTED marker
  grace-period survivability) remains a genuine open design choice, unresolved across 4+ prior passes.
- **satellite-batch-extraction 2026-08-09 (infra tranche)**: extracted the `[SCRIPT] P2` forward-registration CI guard
  into `infra_satellite_ao_dispatch_batch10_2026_08_09.md` todo 1 (`status: active`, conflict-checked against the full
  active corpus, zero competing claims found), per the 2026-08-08 `na-eligibility-audit` pass's own "strong RECLASSIFY
  candidate" flag. Left the `[DATA] P3` PREEMPTED-marker survivability audit untouched — still a genuine undecided
  design choice between 2 named mitigations. Doc stays `assigned_vm: NA` (1 open item remains, judgment-gated).
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid. Re-read end-to-end;
  `grep -cE '^- \[ \]'` = 2, matching (the `[SCRIPT] P2` forward-registration CI guard, and the `[DATA] P3`
  PREEMPTED-marker survivability audit). The `[SCRIPT] P2` item is very well-specified (4 concrete implementation steps,
  filed today directly off the operator's item-78 ruling) and is a strong RECLASSIFY candidate on its own — a
  corpus-wide grep found no conflicting active claim on
  `deployment-service/scripts/quality_gates/check_vm_launcher_prefix_registration.py` or the launcher registries it
  touches. However `assigned_vm` flips whole-doc: the `[DATA] P3` item remains a genuine judgment call (its own
  done-when requires "a mitigation is proposed," and the 2 candidate mitigations named in the evidence — write the
  marker earlier vs. switch to the Compute Operations API fallback — are a real design choice between approaches, not
  yet decided). Doc stays NA as a whole; flagging the `[SCRIPT] P2` item as ready for extraction into a future infra
  batch, not actioned this run (the whole-doc constraint blocks a clean flip).
- **2026-08-08 (operator Q&A round5, infra tranche, item 78)**: Operator ruled (b) — wire into the fleet-level
  `RelaunchPreemptedVm`/exit-code-fleet-monitor actuator. Read the actual current code before filing the follow-up (see
  the flipped todo above for exact file citations): the fleet-level actuator was ALREADY built and cron-scheduled (not
  session-bound) — the 2026-07-26 incident was a registry-coverage gap (`af-backfill-` missing from `DATA_VM_PREFIXES`),
  separately found + fixed 2026-08-04. Filed a scoped `[SCRIPT] P2` follow-up: a forward-looking QG guard so a brand-new
  one-off launcher can never again launch a VM invisible to the fleet monitor (closes the same bug CLASS, not just the
  one instance already fixed). Retagged the primary todo from its self-declared operator/design-judgment status (now
  resolved) to `[x] ✅ DECIDED`.
- **na-eligibility-audit 2026-08-07 (infra tranche)**: KEEP-NA, valid — unchanged since 2026-07-30. Re-read end-to-end;
  `grep -cE '^- \[ \]'` = 2, matching. Primary todo remains a genuine design/judgment call (which reliability model to
  commit to) with no decision made. The secondary P3 audit todo now carries stronger measured evidence (2026-08-04
  entry: 2/2 fresh SPOT preemptions still show no `PREEMPTED` marker even after the hardened write helper) but its own
  done-when ("measured evidence the race is rare, OR a mitigation is proposed") isn't fully met — evidence gathered
  points the opposite way (race is common, not rare), but no mitigation has been proposed/decided yet. Re-flagging as a
  RECLASSIFY-candidate worth a fresh scoping look given the new evidence, not actioned this run.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — Primary todo is explicitly
  self-declared as a design/judgment call (which reliability model to commit to for ad hoc backfill VMs) with no
  decision made yet — stays NA as a whole; the secondary measurement/audit todo is an individually plausible future
  RECLASSIFY candidate, not actioned this run.

- **context-scout 2026-08-03**: refreshed context_scope (5 entries — added
  `deployment-service/scripts/vm/lib/launcher_common.sh`, the shutdown-script template the P3 todo names directly).
- **2026-08-04 (slot 8)** — Fresh evidence for the open P3 "PREEMPTED marker grace-period survivability" audit: two more
  af-backfill SPOT preemptions on 2026-08-03/04 (`af-backfill-20260803-233053`, `af-backfill-20260804-001203`) each
  wrote **NO** `vm-logs/<vm>/PREEMPTED` blob — verified by direct `gcloud storage ls` of both
  `gs://deployment-scripts-central-element-323112/vm-logs/<vm>/` prefixes (only `LAUNCH_PARAMS.json` / `PROGRESS.json` /
  `WATCHDOG_TRACE.log` / `run.log` present). This is **2/2 misses AFTER** the switch to the hardened
  `lc_write_preemption_signal_file` helper (baked VM_NAME/PROJECT + curl-retry upload), so that hardening did NOT close
  the race — the marker write still loses to `--instance-termination-action=DELETE` inside the ~30s grace window (last
  GCS write → `compute.instances.preempted` op start was ~58s and ~24s respectively). Strengthens the case that the
  marker is not a reliable fleet-wide signal; a mitigation (write earlier/more defensively, or make the monitor rely on
  the Compute Operations API `preemption_op_checker` fallback rather than the in-guest blob) is warranted. Cross-ref:
  `/plans/archive/issues/af_backfill_preemption_auto_recovery_not_firing_2026_08_04.md`.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
