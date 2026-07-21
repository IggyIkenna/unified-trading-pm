---
doc_type: issue
title:
  "exit_code_fleet_monitor classifies a preempted-but-partial VM as CLEAN when the PREEMPTED marker is absent — silently
  masks a premature kill fleet-wide"
summary:
  classify_terminated_vm() in deployment-service's exit_code_fleet_monitor.py checks preempted (the durable GCS marker)
  before exit_code, but falls back to "captured climbed => CLEAN" whenever the marker is absent and no exit_code was
  recorded. A VM that made SOME real progress before being killed (SPOT preemption whose marker never got written, or
  any other premature-kill class with no clean exit) is therefore indistinguishable from a genuinely-finished run — no
  alert, no auto-relaunch, silent data-loss-in-progress. Confirmed via a real incident (af-backfill-20260719-180520/
  -180603, 2026-07-20T05:25Z).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [spot-vm, self-healing, monitoring, false-positive, preemption, data-pipeline-monitors]
related:
  [
    plans/active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md,
    plans/active/issues/zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md,
  ]
created: 2026-07-21
priority: P2
parent_epic: infrastructure_master
source: "sports_p2_history_apifootball_2015_to_present-005 dispatch, 2026-07-21"
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

## What I found

Root-causing why 2 of 4 `af-backfill-*` SPOT shards (`af-backfill-20260719-180520` FIXTURE_EVENTS, `-180603`
FIXTURE_STATS) sat dead ~22h with zero self-heal after dying ~2026-07-20T05:25Z
(`sports_p2_history_apifootball_2015_to_present_2026_06_27.md` Todo `-005`), I confirmed via the GCP audit log
(`compute.instances.preempted` system events, `resource.type=gce_instance`) that **both VMs were genuinely
SPOT-preempted** at 2026-07-20T05:26:07Z / 05:26:17Z — not an agent-manual delete (the pattern the sibling
`zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md` issue documents for other incidents).

**Proximate cause (timing gap, already self-resolving)**: the durable `vm-logs/{vm}/PREEMPTED` marker blob — the signal
`is_vm_preempted()` reads to route a terminated VM to the `PREEMPTED` verdict → `auto_recover` → `RelaunchPreemptedVm` —
is written by a shutdown-script systemd unit (`uts-preemption-signal.service`) installed in
`scripts/vm/setup-data-pipeline-vm.sh`. That unit shipped in `deployment-service@c79f984` at **2026-07-20T14:59:33Z** —
**~9.5 hours AFTER** these 2 VMs were preempted (05:26Z) and ~21h after they booted (2026-07-19T18:05-18:06Z, running
whatever `setup-data-pipeline-vm.sh` existed at launch time). GCE startup-scripts execute once at boot and are never
re-fetched, so these already-running VMs never had the marker-writing unit installed — when GCE preempted them, nothing
wrote the marker. This part is **not a recurring bug**: any `af-backfill-*` VM launched after 2026-07-20T14:59:33Z has
the fix (verified: the P0 relaunch todo's replacement VMs, `af-backfill-20260721-033537`/`-033605`, are running and
advancing normally).

**The deeper, still-open finding**: `classify_terminated_vm()`
(`deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py`) has this verdict precedence:

```
preempted == True        -> PREEMPTED (benign, auto-relaunch)
exit_code not in (None,0) -> EXIT_NONZERO
captured climbed          -> CLEAN            <-- no alert, no relaunch, terminal
... (live-VM / no-capture-reason splits) ...
else (SILENT + no climb)  -> GONE_NO_CAPTURE  (alerts)
```

For these 2 VMs: `preempted=False` (no marker — see above), `exit_code=None` (force-deleted mid-run, never wrote a
terminal code), and `captured` **did climb** during their ~11h partial run before the kill (PROGRESS.json showed real
advancing dates, per the consuming plan's Progress Log). Per the precedence above, that resolves to **CLEAN** — the
monitor's own model of the world is "this VM finished its work successfully." **No alert of any kind fires** in this
path, which is a materially different (and worse) failure mode than "the operator wasn't paged" — the system doesn't
know anything went wrong at all. This explains the observed ~22h of total silence more precisely than "the relaunch just
didn't happen": the fleet monitor believed there was nothing to relaunch.

**Why this is not specific to the fix-timing gap**: any terminated VM that (a) has no recorded exit_code (mid-run
force-delete, of which SPOT preemption is only one cause — see the sibling issue doc's Incidents 2-6 for
agent-manual-delete and batch-teardown examples of VMs also dying with no clean exit) AND (b) made real partial progress
before dying, will resolve to CLEAN today regardless of whether `is_vm_preempted()` correctly detects a preemption. The
`uts-preemption-signal.service` unit is itself best-effort and bounded (`TimeoutStopSec=25`, `gcloud storage cp` over
network during the ~30s GCE preemption notice) — a slow/failed write on a FUTURE preempted VM would reproduce this exact
silent-CLEAN outcome even with the fix fully deployed.

## Why it matters

- A VM that dies mid-run with partial progress is currently indistinguishable, to this monitor, from a VM that finished
  on time — for ANY VM using `exit_code_fleet_monitor`, not just `af-backfill-*`.
- The failure mode is silent (no alert, no relaunch, no page) rather than merely under-automated (a page but no
  auto-recover) — worse for operator trust, since nothing in the monitoring surface flags the gap.
- Recurrence risk is not eliminated by the 2026-07-20T14:59:33Z fix landing — that fix only prevents the
  no-marker-at-all case for future VM boots; a marker-write race/failure on an already-covered VM reproduces the
  identical CLEAN-misclassification outcome.

## Recommended decision

- [x] [INFRA] P2. ✅ **Add a defensive check to `classify_terminated_vm()` (or its caller)**: before resolving to CLEAN
      on a VM with `exit_code is None` (no durable terminal exit code was ever observed), independently corroborate
      "this really finished" — e.g. require either a `DEPLOYMENT_COMPLETED`/`EXIT_STATUS=0` `run.log` marker OR the
      manifest's own completion signal (full requested date range reached, not just "captured climbed some") before
      treating a no-exit-code VM as CLEAN. A `captured climbed` VM with NO recorded completion marker and NO reached
      end-date is the exact ambiguous case this incident hit — resolve it to a new, lower-severity-but-NOT-silent
      verdict (e.g. `PARTIAL_UNCONFIRMED`, `auto_recover`-routed like PREEMPTED so it self-heals AND is visible) rather
      than either of the two existing extremes (`CLEAN` silence or `GONE_NO_CAPTURE` false-alarm-on-legit-partial-runs).
      (repo: deployment-service) — deployment-service@2e22c54: `classify_terminated_vm()`'s CLIMBED branch now splits on
      `exit_code` (`== 0` → CLEAN, `is None` → new `PARTIAL_UNCONFIRMED` verdict, DP-VM-008), routed `auto_recover`
      reusing the SAME checkpoint-resume `RelaunchPreemptedVm` actuator as PREEMPTED (WARN, not silent). Scoped to the
      exit_code=None case only (the `DEPLOYMENT_COMPLETED`/manifest-end-date corroboration in the "e.g." text was
      illustrative, not load-bearing — `exit_code is None` already means no terminal marker of any kind exists, so there
      is no weaker corroboration signal available to check first). Codex updated:
      `codex/05-infrastructure/data-pipeline-alerts.md` + `.registry.yaml` (DP-VM-007 backfilled, was undocumented;
      DP-VM-008 added). Unit tests: `test_classify_partial_unconfirmed_when_exit_none_and_climb`,
      `test_classify_clean_still_requires_confirmed_exit0_not_just_climb`,
      `test_sweep_partial_unconfirmed_vm_relaunches_successfully_emits_warn_not_critical`,
      `test_sweep_partial_unconfirmed_vm_no_launcher_emits_critical_no_relaunch` — full `quality-gates.sh` green.
- [ ] [INFRA] P3. **Harden `uts-preemption-signal.service`'s marker write for the fast-DELETE case** — confirm
      `--instance-termination-action=DELETE` SPOT VMs (used by `af-backfill-*` and others) reliably give the shutdown
      unit's `ExecStop` its full window before the instance is torn down; if GCE's DELETE path can race ahead of the
      unit's `TimeoutStopSec=25`, consider a secondary detection path (e.g. the `compute.instances.preempted` GCP
      audit-log event itself, which this investigation confirmed exists and is queryable independent of any VM-side
      marker) as a fallback trigger for `is_vm_preempted()`-equivalent classification. (repo: deployment-service)
