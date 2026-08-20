---
doc_type: issue
title:
  DP-VM-001 exit_code=137 (stall-induced SIGKILL, not OOM) on tradfi-bf-cme-ohlcv-1m-es-2020-20260815-030216 —
  tradfi-bf-cme-ohlcv-1m- launcher family already at the 2/2 relaunch-dispatch bound today, page instead of relaunch
summary: >-
  A data-pipeline fleet monitor detected VM `tradfi-bf-cme-ohlcv-1m-es-2020-20260815-030216` terminated with
  `exit_code=137` — the escalation's own context flags this as a **stall-induced SIGKILL, not an OOM kill** (137 is the
  raw signal-9 exit code shared by both causes; the dispatching monitor distinguished them and reported this one as
  stall-induced). The `tradfi-bf-cme-ohlcv-1m-` launcher family already used its `≤2/(vm-prefix, day)` RB-INFRA-RELAUNCH
  allowance earlier today per the escalation. Whether classed as `DP_VM_EXIT_NONZERO`(OOM) or `DP_VM_STALL`, both
  actuator classes share the identical `≤2/(vm-prefix, day)` bound (`/codex/05-infrastructure/data-pipeline-alerts.md` §
  "self-heal actuator layer" table), and the family is already at that bound — so a further relaunch here would be a
  third blind retry, not new information, independent of which of the two classes applies. No prior issue doc names this
  exact VM (grepped `plans/active/issues/` for the VM name and for `DP-VM-001`; a related-but-distinct prior doc,
  `tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md`, covers a duplicate-launch scope ruling
  for the same `cme-ohlcv-1m-es-2020` shard family from 2026-08-09 — different incident, different root cause).
  Confirmed via `gcloud compute instances list` that this VM is no longer in the live fleet (0 rows) — consistent with a
  terminated/self-deleted VM. This worker did NOT relaunch and did NOT pull `run.log` content to diagnose the
  in-container stall root cause this session — it files this doc and pages the operator per the escalation's explicit
  instruction.
status: open
nature: issue
asset_group: [tradfi]
stage: [meta]
repos: [deployment-service, market-data-processing-service]
scope: [engineer, admin]
tags: [dp-vm-001, exit-code-monitor, tradfi-bf-cme, relaunch-bound, page, data-pipeline-monitors, stall]
related:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/archive/issues/tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md,
    /plans/active/issues/dp_vm_001_mdps_tradfi_2026_exit_nonzero_relaunch_bound_page_2026_08_14.md,
    /plans/active/issues/dp_vm_001_mdps_cefi_2019_exit_nonzero_relaunch_bound_page_2026_08_14.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
context_scope: [/codex/15-runbooks/incidents/rb_infra_relaunch.md, /codex/05-infrastructure/data-pipeline-alerts.md, /plans/active/tradfi_satellite_ao_dispatch_batch15_2026_08_17.md, deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py, deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py, deployment-service/deployment_service/data_pipeline_monitors/_gcs.py]
created: "2026-08-15"
parent_epic: security_and_cross_cutting_master
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
  Escalation agt-4a1f35 (wall_type=data_pipeline_failure, dispatched to slot 5, 2026-08-15). Context carried the finding
  directly: "VM tradfi-bf-cme-ohlcv-1m-es-2020-20260815-030216 terminated with exit_code=137 (stall-induced SIGKILL, not
  OOM) — captured did not complete cleanly... DO NOT RELAUNCH... launcher-family tradfi-bf-cme-ohlcv-1m- already hit 2/2
  relaunch dispatches today (RB-INFRA-RELAUNCH bound)." No separate audit CSV/candidate list was attached ("Filed issue:
  (none — alert carries the details)"). VM confirmed absent from the live fleet this session (`gcloud compute instances
  list --filter="name~tradfi-bf-cme-ohlcv-1m-es-2020-20260815-030216"` returned zero rows).
---

# DP-VM-001 — tradfi-bf-cme-ohlcv-1m-es-2020-20260815-030216 exit_code=137 (stall, not OOM), relaunch-bound, page not relaunch

## What happened

- VM: `tradfi-bf-cme-ohlcv-1m-es-2020-20260815-030216` (asset_group=tradfi, root=ES, year-shard=2020, launcher-family
  prefix `tradfi-bf-cme-ohlcv-1m-`).
- Terminal state: `exit_code=137`, which the dispatching monitor classified as a **stall-induced SIGKILL** (a
  watchdog/heartbeat-timeout kill), not the OOM-killer — a distinction 137 alone can't carry (both share the raw
  signal-9 exit code), but the escalation's context explicitly disambiguates it.
- The `tradfi-bf-cme-ohlcv-1m-` launcher family had already used its `≤2/(vm-prefix, day)` RB-INFRA-RELAUNCH allowance
  today per the dispatching escalation (2/2 dispatches).
- No issue doc previously named this exact VM. A related but distinct prior doc
  (`tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md`) covered a 2026-08-09 duplicate-launch
  scope-ruling incident for the same `cme-ohlcv-1m-es-2020` shard family — different failure mode (concurrent duplicate
  launches), different date, not this exit-137 finding.

## Why this is a PAGE case, not a relaunch

Per `/codex/05-infrastructure/data-pipeline-alerts.md` § "self-heal actuator layer", both `DP_VM_EXIT_NONZERO` (137/OOM,
via `relaunch_backfill_vm.py`) and `DP_VM_STALL`/hung (via `relaunch_stalled_vm.py`) actuators share the identical
`≤2/(vm-prefix, day)` bound. Regardless of which class this finding is (the escalation says stall, not OOM), the family
is already at that bound for today — `RB-INFRA-RELAUNCH`'s own guidance ("if it re-fails the SAME way twice... STOP
relaunching, file an issue") points the same direction: stop and page. The root-cause-diagnosed carve-out (ruled
2026-08-02) does not apply here — no root cause has been diagnosed or fixed this session, so this would be a third blind
retry, not genuinely new information.

## What this worker did NOT do

- Did not relaunch `tradfi-bf-cme-ohlcv-1m-es-2020-20260815-030216` or any other `tradfi-bf-cme-ohlcv-1m-` VM.
- Did not pull `run.log` content for this VM (the VM is gone from the live fleet; a GCS SDK read of its archived
  `vm-logs/` blob is the next diagnostic step for whoever picks this up — use
  `deployment_service.data_pipeline_monitors._gcs.read_text`/`read_terminal_exit_code`, never a subprocess
  `gsutil`/`gcloud storage` call, per the workspace GCS-object-ops hard rule).
- Did not diagnose the in-container stall root cause (candidate causes per the DP-VM-003/stall runbook pattern: an
  unbounded outbound HTTP call lacking `timeout=`, or a per-shard hang in the CME OHLCV 1m capture loop) — that is the
  actual open work this doc tracks.

## Recommended decision (for the operator)

1. Confirm whether the `cme-ohlcv-1m-es-2020` shard's data is still outstanding (check the manifest for
   asset_group=tradfi, venue=CME, root=ES, year=2020, timeframe=1m OHLCV coverage) — if genuinely still missing, a
   relaunch is warranted but should wait for either (a) the family's daily `≤2/(vm-prefix,day)` bound to reset, or (b) a
   root-cause diagnosis of the stall first (the root-cause-diagnosed carve-out in `RB-INFRA-RELAUNCH`).
2. Pull `run.log` for `tradfi-bf-cme-ohlcv-1m-es-2020-20260815-030216` via the SDK helpers above to identify the stall's
   actual failure signature (unbounded HTTP hang, missing timeout, per-shard deadlock) before any next relaunch attempt
   for this or sibling `tradfi-bf-cme-ohlcv-1m-` shards.

## Todos

- [ ] [OPERATOR] P1. Decide relaunch-vs-wait for `tradfi-bf-cme-ohlcv-1m-es-2020-20260815-030216`'s shard
      (tradfi/CME/ES/2020 1m OHLCV) per the recommended decision above; the `tradfi-bf-cme-ohlcv-1m-` family relaunch
      bound is already exhausted for today (2/2).
- [x] ✅ [BACKEND] P2. **CONSOLIDATED 2026-08-17 (na-eligibility-audit, tradfi tranche, dispatch agt-d99b5c) — folded
      into `tradfi_satellite_ao_dispatch_batch15_2026_08_17.md` Todo 2** (that todo covers this VM together with the
      `btc-2020` sibling stall — do not double-dispatch a separate run.log pull for this VM; the batch todo already
      accounts for this doc's own partial pull below — 1561 lines, confirmed genuine `WORKER_STALLED`, actual hung
      call still unidentified). Original ask: pull + read `run.log` for
      `tradfi-bf-cme-ohlcv-1m-es-2020-20260815-030216` via
      `deployment_service.data_pipeline_monitors._gcs.read_text`/`read_terminal_exit_code` (SDK, never subprocess) to
      diagnose the stall root cause; fix at the root if it's a code defect; cross-check other
      `tradfi-bf-cme-ohlcv-1m-` shards for the same signature.

## Progress Log

- 2026-08-15 (slot 5, data_pipeline_failure escalation agt-4a1f35): Received escalation for DP-VM-001
  `tradfi-bf-cme-ohlcv-1m-es-2020-20260815-030216` exit_code=137, flagged by the escalation as stall-induced, not OOM.
  Checked for an existing issue doc naming this VM — none found (grepped `plans/active/issues/*.md` for the VM name, the
  shard-family prefix, and `DP-VM-001`; found a related-but-distinct 2026-08-09 duplicate-launch scope doc for the same
  shard family, and two same-shape sibling `DP-VM-001` relaunch-bound-page docs from 2026-08-14 for a different launcher
  family (`mdps-tradfi-`/`mdps-cefi-`)). Confirmed via `gcloud compute instances list` the VM is no longer in the live
  fleet (0 rows). Per RB-INFRA-RELAUNCH, both the OOM and stall actuator classes share the identical
  `≤2/(vm-prefix, day)` bound, and the `tradfi-bf-cme-ohlcv-1m-` family was already reported at that bound (2/2) — did
  not relaunch. Filed this issue doc and paging the operator via `/blocked` per the escalation's explicit instruction.
  No code changed this session.

- **na-eligibility-audit 2026-08-16** (tradfi tranche, dispatch agt-45ad7b): **KEEP-NA, valid.** Todo 1 is an explicit
  [OPERATOR] relaunch-vs-wait judgment call. Todo 2 names a candidate hypothesis but is not yet a bounded, committed
  action. Genuinely operator-gated. assigned_vm unchanged.
- **2026-08-16 (slot 12, batch14 todo 2 — cross-VM confirm/refute).** Pulled this VM's `run.log` via `_gcs.read_text`
  — only **1561 lines / 151KB** (this VM stalled ~4 minutes after start, so the log is short by construction).
  Greped for `No adapter for tradfi/<data_type>`: **ZERO occurrences.** **REFUTED — this VM does NOT share the
  `mdps-tradfi-` stale-tarball root cause**; it never got far enough into per-date processing to hit that codepath
  at all. Confirms the doc's existing classification: the log tail shows `watchdog exiting iter=65 reason=stall`,
  `[vm-exec] DEPLOYMENT_FAILED cause=stall reason=WORKER_STALLED mode=no-progress-marker stalled_for=3939
  threshold=3900`, `exit_code=137` — a genuine stall-induced SIGKILL, not OOM and not an adapter-registry crash. The
  log also carries a kernel stall-dump stack trace, but it's for the `tee` wrapper process (`pid=15455 comm=tee`,
  blocked in `anon_pipe_read`), not the actual worker process — so this pull does NOT identify which call in the
  CME OHLCV 1m capture path actually hung; that remains open work for the BACKEND todo above (candidate: an
  unbounded outbound call lacking `timeout=`), not resolved by this cross-VM check.
**context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
- **na-eligibility-audit 2026-08-17** (tradfi tranche, dispatch agt-d99b5c): **RECLASSIFY, per-todo split.** Todo 2
  consolidated into `tradfi_satellite_ao_dispatch_batch15_2026_08_17.md` Todo 2 alongside the `btc-2020` sibling —
  see checkbox above. Todo 1 (operator relaunch decision) stays genuinely gated. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
