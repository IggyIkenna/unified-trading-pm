---
doc_type: issue
title:
  DP-VM-001 exit_code=137 (stall-induced SIGKILL, not OOM) on tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2020-20260816-162556 —
  tradfi-bf-cme-ohlcv-1m- launcher family already at the 2/2 relaunch-dispatch bound today, page instead of relaunch
summary: >-
  A data-pipeline fleet monitor detected VM `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2020-20260816-162556` terminated with
  `exit_code=137` — the escalation's own context flags this as a **stall-induced SIGKILL, not an OOM kill**. The
  `tradfi-bf-cme-ohlcv-1m-` launcher family already used its `≤2/(vm-prefix, day)` RB-INFRA-RELAUNCH allowance today
  (per the escalation's own context: "launcher-family tradfi-bf-cme-ohlcv-1m- already hit 2/2 relaunch dispatches
  today"). No prior issue doc names this exact VM (grepped `plans/active/issues/` for the VM name and `DP-VM-001`; the
  only same-family docs found are dated 2026-08-15, a different day, naming different VMs `es-2020-20260815-030216`
  and `g01-6a-6l-2020-20260815-200147`). Confirmed via
  `gcloud compute instances list --filter="name~tradfi-bf-cme-ohlcv-1m"` that this specific VM is no longer in the
  live fleet — the currently-running `tradfi-bf-cme-ohlcv-1m-*` instances all carry `20260816-1804xx`-`1809xx`
  timestamps (a separate, already-in-flight relaunch wave for other shards in the family, not this VM). This worker
  did NOT relaunch and did NOT pull `run.log` content to diagnose the in-container stall root cause this session — it
  files this doc and pages the operator per the escalation's explicit instruction.
status: resolved
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
    /plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_exit137_stall_relaunch_bound_page_2026_08_15.md,
    /plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_es_2020_exit137_stall_relaunch_bound_page_2026_08_15.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
context_scope: [/codex/15-runbooks/incidents/rb_infra_relaunch.md, /codex/05-infrastructure/data-pipeline-alerts.md, deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py, deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py]
created: "2026-08-16"
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
  Escalation agt-072f3f (wall_type=data_pipeline_failure, dispatched to slot 8, 2026-08-16). Context carried the
  finding directly: "VM tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2020-20260816-162556 terminated with exit_code=137
  (stall-induced SIGKILL, not OOM) — captured did not complete cleanly... DO NOT RELAUNCH...
  launcher-family tradfi-bf-cme-ohlcv-1m- already hit 2/2 relaunch dispatches today (RB-INFRA-RELAUNCH bound)." No
  separate audit CSV/candidate list was attached ("Filed issue: (none — alert carries the details)"). VM confirmed
  absent from the live fleet this session (`gcloud compute instances list --filter="name~tradfi-bf-cme-ohlcv-1m"`
  shows only a distinct, already-in-flight relaunch wave with different timestamps).
---

# DP-VM-001 — tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2020-20260816-162556 exit_code=137 (stall, not OOM), relaunch-bound, page not relaunch

## What happened

- VM: `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2020-20260816-162556` (asset_group=tradfi, launcher-family prefix
  `tradfi-bf-cme-ohlcv-1m-`, shard token `g01-6a-6l-2020`).
- Terminal state: `exit_code=137`, which the dispatching monitor classified as a **stall-induced SIGKILL** (a
  watchdog/heartbeat-timeout kill), not the OOM-killer — a distinction 137 alone can't carry, but the escalation's
  context explicitly disambiguates it.
- The `tradfi-bf-cme-ohlcv-1m-` launcher family had already used its `≤2/(vm-prefix, day)` RB-INFRA-RELAUNCH
  allowance today (per this escalation's own context: "already hit 2/2 relaunch dispatches today").
- No issue doc previously named this exact VM. Two same-family, prior-day (2026-08-15) sibling incidents exist for
  different VMs/shards (`es-2020-20260815-030216`, `g01-6a-6l-2020-20260815-200147`) — this is a fresh, same-shard
  recurrence one day later, on a fleet that is already mid-relaunch for other shards in the family (confirmed live:
  multiple `tradfi-bf-cme-ohlcv-1m-*` VMs RUNNING with `20260816-1804xx`-`1809xx` launch timestamps, none matching
  this VM or the `g01-6a-6l-2020` shard).

## Why this is a PAGE case, not a relaunch

Per `/codex/05-infrastructure/data-pipeline-alerts.md` § "self-heal actuator layer", both `DP_VM_EXIT_NONZERO`
(137/OOM, via `relaunch_backfill_vm.py`) and `DP_VM_STALL`/hung (via `relaunch_stalled_vm.py`) actuators share the
identical `≤2/(vm-prefix, day)` bound. The family is already at that bound for today per the escalation's own
context — `RB-INFRA-RELAUNCH`'s own guidance ("if it re-fails the SAME way twice... STOP relaunching, file an
issue") points the same direction: stop and page. The root-cause-diagnosed carve-out (ruled 2026-08-02) does not
apply — no root cause has been diagnosed or fixed this session, so a further relaunch would be a blind retry, not
genuinely new information. A `g01-6a-6l-2020` stall recurring the day after the same shard already stalled once
(2026-08-15) is itself a signal worth the operator's attention — this could be a shard-specific defect (e.g. a
poison instrument/date range in that group/chain/year combination) rather than a random fleet-wide flake.

## What this worker did NOT do

- Did not relaunch `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2020-20260816-162556` or any other `tradfi-bf-cme-ohlcv-1m-` VM.
- Did not pull `run.log` content for this VM (the VM is gone from the live fleet; a GCS SDK read of its archived
  `vm-logs/` blob is the next diagnostic step for whoever picks this up — use
  `deployment_service.data_pipeline_monitors._gcs.read_text`/`read_terminal_exit_code`, never a subprocess
  `gsutil`/`gcloud storage` call, per the workspace GCS-object-ops hard rule).
- Did not diagnose the in-container stall root cause, and did not cross-check whether this stall shares the same
  signature as the 2026-08-15 `g01-6a-6l-2020` stall on the SAME shard token — that cross-check plus the actual
  root-cause diagnosis is the open work this doc (together with its 2026-08-15 sibling) tracks.

## Recommended decision (for the operator)

1. Confirm whether the `g01-6a-6l-2020` shard's data is still outstanding (check the manifest for asset_group=tradfi,
   venue=CME, timeframe=1m OHLCV, the instrument set covered by group `g01` chains `6a`-`6l`, year=2020) — if
   genuinely still missing, a relaunch is warranted but should wait for either (a) the family's daily
   `≤2/(vm-prefix,day)` bound to reset, or (b) a root-cause diagnosis of the stall first.
2. Pull `run.log` for both the 2026-08-15 (`g01-6a-6l-2020-20260815-200147`) and 2026-08-16
   (`g01-6a-6l-2020-20260816-162556`) attempts of the SAME shard via the SDK helpers above and compare failure
   signatures — a same-shard repeat stall one day apart strongly suggests a shard-specific poison input rather than
   a generic fleet flake, which would change the fix from "bound the HTTP call" to "isolate/skip the poison
   instrument-date and retry the rest."

## Todos

- [x] ✅ [OPERATOR] P1. **CLOSED 2026-08-17 (na-eligibility-audit, tradfi tranche, dispatch agt-d99b5c) — evidence:
      this doc's own 2026-08-17 Progress Log correction entry below.** Root cause is now known: the tracked
      Databento CME `402 account_delinquent_invoice` billing block
      (`tradfi_databento_account_billing_suspended_2026_08_09.md`, still `status: blocked`) — a relaunch will hit
      the identical wall until that P0 clears, so this is no longer a live relaunch-vs-wait decision, it's a
      wait-on-billing dependency tracked in that doc. Original ask: decide relaunch-vs-wait for this shard.
- [x] ✅ [BACKEND] P2. **CLOSED 2026-08-17 (na-eligibility-audit, tradfi tranche, dispatch agt-d99b5c) — evidence:
      this doc's own 2026-08-17 Progress Log correction entry below.** Root cause identified: the Databento billing
      block above, not a shared code defect and not a poison-instrument/date issue (this todo's own two candidate
      branches) — the adapter returned promptly with a 402, it did not hang, so `asyncio.wait_for` bounding is very
      unlikely to be the real fix per that same correction entry. No code fix needed here. Original ask:
      pull+compare run.log for both same-shard attempts and fix at the root.

## Progress Log

- 2026-08-16 (slot 8, data_pipeline_failure escalation agt-072f3f): Received escalation for DP-VM-001
  `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2020-20260816-162556` exit_code=137, flagged by the escalation as stall-induced,
  not OOM. Checked for an existing issue doc naming this VM — none found; found two same-family sibling docs dated
  2026-08-15 (different VMs, one of which was the SAME shard token `g01-6a-6l-2020` on a prior day), both already at
  the family's 2/2 relaunch bound on their respective days. Confirmed via
  `gcloud compute instances list --filter="name~tradfi-bf-cme-ohlcv-1m"` that this exact VM is no longer in the live
  fleet — the live fleet shows only a separate, already-in-flight relaunch wave (different timestamps, different
  shards) for the family. Per RB-INFRA-RELAUNCH, did not relaunch. Filed this issue doc and paging the operator via
  `/blocked` per the escalation's explicit instruction. No code changed this session.

- **na-eligibility-audit 2026-08-16** (tradfi tranche, dispatch agt-45ad7b): **KEEP-NA, valid.** Todo 1 is an explicit
  [OPERATOR] relaunch-vs-wait judgment call. Todo 2 offers branching candidate hypotheses, not yet a committed bounded
  action. Genuinely operator-gated. assigned_vm unchanged.

- **2026-08-17 (slot 4, data_pipeline_failure escalation agt-5af8eb) — CORRECTION to Todo 2's hypothesis, same
  shard, third same-day/next-day occurrence.** A fresh DP-VM-001 finding on the SAME shard token
  (`tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2020-20260816-220209`) let this worker pull `run.log` — something this doc's
  own session and its 2026-08-15 sibling both explicitly skipped. Root cause is neither "a shared code defect" nor
  "a poison-instrument/date issue specific to this shard" (Todo 2's two branches): it's the already-tracked
  Databento CME/`GLBX.MDP3` `402 account_delinquent_invoice` billing block
  (`tradfi_databento_account_billing_suspended_2026_08_09.md`, still `status: blocked`), which stopped forward
  progress on `2020-06-10` and let the in-VM stall watchdog fire ~65min later. `g01-6a-6l-2020` isn't special — any
  CME-sourced shard needing dates past whatever the account last paid through will hit the identical wall. Full
  writeup:
  `/plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_20260816_220209_databento_cme_billing_rootcause_2026_08_17.md`.
  Leaving this doc's own Todo 1/Todo 2 checkboxes as-is (not this worker's VM/session to close) but flagging Todo 2's
  "bound the offending call with `asyncio.wait_for`" branch as very unlikely to be the real fix — the adapter
  returned promptly with a 402, it did not hang.
**context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
- **na-eligibility-audit 2026-08-17** (tradfi tranche, dispatch agt-d99b5c): **KEEP-NA-stale-items, closed with
  evidence.** Both open items are resolved-in-substance by this doc's own 2026-08-17 correction entry above (root
  cause = tracked Databento billing block, not a code defect or poison-instrument) — closed both, see checkboxes
  above. Doc now has 0 open todos — `status: resolved` above, archiving per the standard 6-step ritual
  (`doc_type: issue` → flat `plans/archive/issues/` per `issue-doc-lifecycle.md`). Referrers fixed: the 4 still-active
  sibling docs that cite this one.
