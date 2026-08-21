---
doc_type: issue
title:
  DP-VM-001 exit_code=137 (stall-induced SIGKILL, not OOM) on tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2021-20260816-200155 —
  tradfi-bf-cme-ohlcv-1m- launcher family already at the 2/2 relaunch-dispatch bound today, page instead of relaunch
summary: >-
  A data-pipeline fleet monitor detected VM `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2021-20260816-200155` terminated with
  `exit_code=137` — the escalation's own context flags this as a **stall-induced SIGKILL, not an OOM kill**. The
  `tradfi-bf-cme-ohlcv-1m-` launcher family already used its `≤2/(vm-prefix, day)` RB-INFRA-RELAUNCH allowance today
  (per the escalation's own context: "launcher-family tradfi-bf-cme-ohlcv-1m- already hit 2/2 relaunch dispatches
  today"). No prior issue doc names this exact VM (grepped `plans/active/issues/` for `200155`, `g01-6a-6l-2021`,
  `g01_6a_6l_2021`, and `DP-VM-001` — the only same-family docs found target the **2020** shard token
  (`g01-6a-6l-2020`, `es-2020`, `btc-2020`), dated 2026-08-15/2026-08-16; this is a distinct **2021** shard, a fresh
  incident, not a duplicate). `gcloud compute instances list --filter="name~tradfi-bf-cme-ohlcv-1m"` shows the failed
  VM is gone from the live fleet, but a VM matching the **exact same shard token**,
  `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2021-20260816-220230`, is currently RUNNING — launched ~2h01m after the failure,
  alongside six sibling VMs spanning `g01-6a-6l-{2020,2022,2023,2024,2025,2026}` and `g02-6m-cl-2020`, all with
  creation timestamps within ~2 minutes of each other (`220209`-`220428`). The tight clustering across many distinct
  year-shards points to a scheduled fleet-wide multi-year launch wave for this launcher family, not a targeted
  relaunch of the failed VM specifically — but since it happens to cover the identical shard, it may already resolve
  the gap; this worker did NOT verify the running VM's `LAUNCH_PARAMS.json` against the failed VM's date range or
  check its `PROGRESS.json` for an advancing checkpoint (per RB-INFRA-RELAUNCH's "verify a genuine replacement
  exists" guidance) — that check is the fastest way to tell whether this issue is already self-resolving. This
  worker did NOT relaunch and did NOT pull `run.log` content to diagnose the in-container stall root cause this
  session — it files this doc and pages the operator per the escalation's explicit instruction.
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
    /plans/archive/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_exit137_stall_relaunch_bound_page_2026_08_16.md,
    /plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_exit137_stall_relaunch_bound_page_2026_08_15.md,
    /plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_es_2020_exit137_stall_relaunch_bound_page_2026_08_15.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
context_scope: [/codex/15-runbooks/incidents/rb_infra_relaunch.md, /codex/05-infrastructure/data-pipeline-alerts.md, /plans/active/tradfi_satellite_ao_dispatch_batch15_2026_08_17.md, deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py, deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py, deployment-service/deployment_service/data_pipeline_monitors/_gcs.py]
created: "2026-08-16"
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
  Escalation agt-9d6668 (wall_type=data_pipeline_failure, dispatched to slot 5, 2026-08-16). Context carried the
  finding directly: "VM tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2021-20260816-200155 terminated with exit_code=137
  (stall-induced SIGKILL, not OOM) — captured did not complete cleanly... DO NOT RELAUNCH...
  launcher-family tradfi-bf-cme-ohlcv-1m- already hit 2/2 relaunch dispatches today (RB-INFRA-RELAUNCH bound)." No
  separate audit CSV/candidate list was attached ("Filed issue: (none — alert carries the details)"). VM confirmed
  absent from the live fleet this session; a same-shard-token VM is RUNNING under a fresh timestamp as part of a
  wider multi-year launch wave (`gcloud compute instances list --filter="name~tradfi-bf-cme-ohlcv-1m"`).
---

# DP-VM-001 — tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2021-20260816-200155 exit_code=137 (stall, not OOM), relaunch-bound, page not relaunch

## What happened

- VM: `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2021-20260816-200155` (asset_group=tradfi, launcher-family prefix
  `tradfi-bf-cme-ohlcv-1m-`, shard token `g01-6a-6l-2021`).
- Terminal state: `exit_code=137`, which the dispatching monitor classified as a **stall-induced SIGKILL** (a
  watchdog/heartbeat-timeout kill), not the OOM-killer — a distinction 137 alone can't carry, but the escalation's
  context explicitly disambiguates it.
- The `tradfi-bf-cme-ohlcv-1m-` launcher family had already used its `≤2/(vm-prefix, day)` RB-INFRA-RELAUNCH
  allowance today (per this escalation's own context: "already hit 2/2 relaunch dispatches today").
- No issue doc previously named this exact VM or shard. All same-family docs found (2026-08-15/16) target the
  **2020** shard token (`g01-6a-6l-2020`, `es-2020`, `btc-2020`) — this is a fresh, distinct **2021**-shard
  incident, not a recurrence of the already-tracked 2020 problem.

## A same-shard VM is already RUNNING under a fresh timestamp — verify before assuming this is unresolved

- `gcloud compute instances list --filter="name~tradfi-bf-cme-ohlcv-1m"` (this session) shows the failed VM gone,
  but `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2021-20260816-220230` is RUNNING — same shard token, launched ~2h01m after
  the failure (`200155` → `220230`).
- It is one of **eight** VMs in the family that all appeared within a ~2-minute window
  (`220209`-`220428`): `g01-6a-6l-{2020,2021,2022,2023,2024,2025,2026}` + `g02-6m-cl-2020`. The tight clustering
  across seven different YEAR shards of the same group/chain-range, launched simultaneously, looks like a
  **scheduled fleet-wide multi-year launch wave** for this launcher family rather than a targeted relaunch of the
  one failed VM — but it happens to cover the exact shard that failed, so it may already be retrying/completing the
  gap on its own.
- Per RB-INFRA-RELAUNCH's "verify a genuine replacement exists" guidance: this worker did **not** check the running
  VM's `LAUNCH_PARAMS.json` (date range match) or `PROGRESS.json` (advancing checkpoint) — that is the fastest way
  to determine whether this finding is already self-resolving before anyone spends more effort on it. Flagging this
  explicitly so the operator (or whoever picks up the todo below) checks it FIRST, before diagnosing the stall.

## Why this is a PAGE case, not a relaunch

Per `/codex/05-infrastructure/data-pipeline-alerts.md` § "self-heal actuator layer", both `DP_VM_EXIT_NONZERO`
(137/OOM, via `relaunch_backfill_vm.py`) and `DP_VM_STALL`/hung (via `relaunch_stalled_vm.py`) actuators share the
identical `≤2/(vm-prefix, day)` bound. The family is already at that bound for today per the escalation's own
context — `RB-INFRA-RELAUNCH`'s own guidance ("if it re-fails the SAME way twice... STOP relaunching, file an
issue") points the same direction: stop and page. The root-cause-diagnosed carve-out (ruled 2026-08-02) does not
apply — no root cause has been diagnosed or fixed this session, so a further relaunch would be a blind retry, not
genuinely new information. Additionally, a manual relaunch right now would risk duplicating the already-RUNNING
same-shard VM noted above.

## What this worker did NOT do

- Did not relaunch `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2021-20260816-200155` or any other `tradfi-bf-cme-ohlcv-1m-` VM.
- Did not pull `run.log` content for the failed VM (it is gone from the live fleet; a GCS SDK read of its archived
  `vm-logs/` blob is the next diagnostic step for whoever picks this up — use
  `deployment_service.data_pipeline_monitors._gcs.read_text`/`read_terminal_exit_code`, never a subprocess
  `gsutil`/`gcloud storage` call, per the workspace GCS-object-ops hard rule).
- Did not check `LAUNCH_PARAMS.json`/`PROGRESS.json` for the currently-RUNNING `g01-6a-6l-2021-20260816-220230` VM
  to confirm it is a genuine replacement covering the same date range (see section above).
- Did not diagnose the in-container stall root cause, and did not cross-check whether this stall shares the same
  signature as the 2026-08-15/16 `g01-6a-6l-2020` stalls (same group/chain-range, different year) — that cross-check
  plus the actual root-cause diagnosis is the open work this doc tracks.

## Recommended decision (for the operator)

1. First, check whether `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2021-20260816-220230` (currently RUNNING) already covers
   the failed VM's date range and is progressing — if so, this finding may already be resolving itself and no
   further relaunch action is needed; just track it to completion.
2. If NOT a genuine replacement, confirm whether the `g01-6a-6l-2021` shard's data is still outstanding (check the
   manifest for asset_group=tradfi, venue=CME, timeframe=1m OHLCV, instrument set covered by group `g01`
   chains `6a`-`6l`, year=2021) — if genuinely still missing and not otherwise covered, a relaunch is warranted but
   should wait for either (a) the family's daily `≤2/(vm-prefix,day)` bound to reset, or (b) a root-cause diagnosis
   of the stall first.
3. Pull `run.log` for the failed `g01-6a-6l-2021-20260816-200155` attempt and compare against the 2020-shard stall
   signatures already under investigation in the sibling docs — a repeat stall shape across multiple years of the
   same group/chain-range (`g01-6a-6l-*`) would point at a shared code defect (e.g. an unbounded HTTP call) rather
   than a per-shard poison input, changing the fix priority.

## Todos

- [ ] [OPERATOR] P1. Decide relaunch-vs-wait for `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2021-20260816-200155`'s shard
      (tradfi/CME/g01-6a-6l/2021 1m OHLCV) per the recommended decision above; the `tradfi-bf-cme-ohlcv-1m-` family
      relaunch bound is already exhausted for today (2/2, per this escalation's own context). Check the
      already-RUNNING `g01-6a-6l-2021-20260816-220230` VM FIRST — it may already be resolving this.
- [x] ✅ [BACKEND] P2. **EXTRACTED 2026-08-17 (na-eligibility-audit, tradfi tranche, dispatch agt-d99b5c) →
      `tradfi_satellite_ao_dispatch_batch15_2026_08_17.md` Todo 4** (reworded there to check the confirmed
      Databento CME billing-block signature FIRST, before this todo's original two branches — the sibling
      2020-shard `g01-6a-6l` stalls both turned out to be billing-caused, not code defects). Original ask: pull +
      read `run.log` for `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2021-20260816-200155`, compare its failure signature
      against the 2020-shard stalls, and fix at the root — if it's a shared code defect across `g01-6a-6l-*` years,
      bound the offending call with `asyncio.wait_for` at the per-shard level; if a poison-instrument/date issue,
      isolate + skip it.

## Progress Log

- **na-eligibility-audit 2026-08-17** (tradfi tranche, dispatch agt-d99b5c): **RECLASSIFY, per-todo split.** Todo 2
  (run.log pull+diagnose) is bounded/deterministic — extracted, reworded to check the now-confirmed billing-block
  signature first (see checkbox above). Todo 1 (operator relaunch decision, including checking the already-running
  replacement VM) stays genuinely gated. Doc stays `assigned_vm: NA`.
- 2026-08-16 (slot 5, data_pipeline_failure escalation agt-9d6668): Received escalation for DP-VM-001
  `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2021-20260816-200155` exit_code=137, flagged by the escalation as stall-induced,
  not OOM. Checked for an existing issue doc naming this VM/shard — none found (all same-family docs target the
  2020 shard). Confirmed via `gcloud compute instances list --filter="name~tradfi-bf-cme-ohlcv-1m"` that this exact
  VM is gone from the live fleet, but found a same-shard-token VM (`g01-6a-6l-2021-20260816-220230`) currently
  RUNNING as part of an 8-VM, ~2-minute-clustered multi-year launch wave — flagged as a possible self-resolving
  case, not verified this session. Per RB-INFRA-RELAUNCH, did not relaunch. Filed this issue doc and paging the
  operator via `/blocked` per the escalation's explicit instruction. No code changed this session.
**context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
