---
doc_type: issue
title:
  DP-VM-001 exit_code=137 (stall-induced SIGKILL, not OOM) on tradfi-bf-cme-ohlcv-1m-btc-2020-20260816-180410 —
  tradfi-bf-cme-ohlcv-1m- launcher family already at the 2/2 relaunch-dispatch bound today, page instead of relaunch
summary: >-
  A data-pipeline fleet monitor detected VM `tradfi-bf-cme-ohlcv-1m-btc-2020-20260816-180410` terminated with
  `exit_code=137` — the escalation's own context flags this as a **stall-induced SIGKILL, not an OOM kill**. The
  `tradfi-bf-cme-ohlcv-1m-` launcher family already used its `≤2/(vm-prefix, day)` RB-INFRA-RELAUNCH allowance today
  (per the escalation's own context: "launcher-family tradfi-bf-cme-ohlcv-1m- already hit 2/2 relaunch dispatches
  today"). No prior issue doc names this exact VM (grepped `plans/active/issues/` for `tradfi-bf-cme-ohlcv-1m-btc`,
  `cme-ohlcv-1m-btc`, and the VM's timestamp `20260816-180410` — 0 hits). Three same-family sibling docs exist, all
  different VMs/shards: two dated 2026-08-15 (`es-2020-20260815-030216`, `g01-6a-6l-2020-20260815-200147`) and one
  dated today 2026-08-16 (`g01-6a-6l-2020-20260816-162556`). Confirmed via
  `gcloud compute instances list --filter="name~tradfi-bf-cme-ohlcv-1m"` that this VM is no longer in the live
  fleet — unlike the `g01-6a-6l-2020-20260816-162556` sibling incident (whose live-fleet check found an ambiguous
  overlap with an in-flight relaunch wave for other shards), this VM's `btc` shard token does not appear anywhere in
  the current live fleet at all: the active wave covers only groups `g01`-`g07` (6a/6l, 6m/cl, ct/hg, ho/ng, nkd/rty,
  si/xap, xau/zc) across multiple years, zero `btc`-tagged instances running — the `btc-2020` shard is simply
  stopped, not mid-retry. This worker did NOT relaunch and did NOT pull `run.log` content to diagnose the
  in-container stall root cause this session — it files this doc and pages the operator per the escalation's
  explicit instruction.
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
    /plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_exit137_stall_relaunch_bound_page_2026_08_16.md,
    /plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_exit137_stall_relaunch_bound_page_2026_08_15.md,
    /plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_es_2020_exit137_stall_relaunch_bound_page_2026_08_15.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
context_scope:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py,
    deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py,
  ]
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
  Escalation agt-fc0533 (wall_type=data_pipeline_failure, dispatched to slot 1, 2026-08-16). Context carried the
  finding directly: "VM tradfi-bf-cme-ohlcv-1m-btc-2020-20260816-180410 terminated with exit_code=137
  (stall-induced SIGKILL, not OOM) — captured did not complete cleanly... DO NOT RELAUNCH...
  launcher-family tradfi-bf-cme-ohlcv-1m- already hit 2/2 relaunch dispatches today (RB-INFRA-RELAUNCH bound)." No
  separate audit CSV/candidate list was attached ("Filed issue: (none — alert carries the details)"). VM confirmed
  absent from the live fleet this session (`gcloud compute instances list --filter="name~tradfi-bf-cme-ohlcv-1m"`
  shows only a distinct, already-in-flight relaunch wave for OTHER instrument groups, no `btc` shard present at all).
---

# DP-VM-001 — tradfi-bf-cme-ohlcv-1m-btc-2020-20260816-180410 exit_code=137 (stall, not OOM), relaunch-bound, page not relaunch

## What happened

- VM: `tradfi-bf-cme-ohlcv-1m-btc-2020-20260816-180410` (asset_group=tradfi, launcher-family prefix
  `tradfi-bf-cme-ohlcv-1m-`, shard token `btc-2020`).
- Terminal state: `exit_code=137`, which the dispatching monitor classified as a **stall-induced SIGKILL** (a
  watchdog/heartbeat-timeout kill), not the OOM-killer — a distinction 137 alone can't carry, but the escalation's
  context explicitly disambiguates it.
- The `tradfi-bf-cme-ohlcv-1m-` launcher family had already used its `≤2/(vm-prefix, day)` RB-INFRA-RELAUNCH
  allowance today (per this escalation's own context: "already hit 2/2 relaunch dispatches today") — the SAME
  family-wide bound the `g01-6a-6l-2020-20260816-162556` sibling incident (filed earlier today, same launcher
  family) also hit.
- No prior issue doc names this exact VM or the `btc-2020` shard token (grepped `plans/active/issues/` for
  `tradfi-bf-cme-ohlcv-1m-btc`, `cme-ohlcv-1m-btc`, and the VM's timestamp `20260816-180410` — 0 hits). Three
  same-family sibling docs exist, all different VMs/shards: two dated 2026-08-15 (`es-2020-20260815-030216`,
  `g01-6a-6l-2020-20260815-200147`) and one dated today 2026-08-16 (`g01-6a-6l-2020-20260816-162556`).
- Confirmed via `gcloud compute instances list --filter="name~tradfi-bf-cme-ohlcv-1m"` that this VM is no longer in
  the live fleet. Unlike the `g01-6a-6l-2020-20260816-162556` sibling incident (whose live-fleet check found an
  ambiguous overlap with an in-flight relaunch wave for OTHER shards), this VM's `btc` shard token does **not**
  appear anywhere in the current live fleet at all — the fleet's active wave covers only groups `g01`-`g07` (CME
  futures/currency/metal/agri groups: 6a/6l, 6m/cl, ct/hg, ho/ng, nkd/rty, si/xap, xau/zc) across multiple years,
  with zero `btc`-tagged instances running. The `btc-2020` shard is not currently being retried by any in-flight
  wave — it is simply stopped.

## Why this is a PAGE case, not a relaunch

Per `/codex/05-infrastructure/data-pipeline-alerts.md` § "self-heal actuator layer", both `DP_VM_EXIT_NONZERO`
(137/OOM, via `relaunch_backfill_vm.py`) and `DP_VM_STALL`/hung (via `relaunch_stalled_vm.py`) actuators share the
identical `≤2/(vm-prefix, day)` bound. The family is already at that bound for today per the escalation's own
context — `RB-INFRA-RELAUNCH`'s own guidance ("if it re-fails the SAME way twice... STOP relaunching, file an
issue") points the same direction: stop and page. The root-cause-diagnosed carve-out (ruled 2026-08-02) does not
apply — no root cause has been diagnosed or fixed this session, so a further relaunch would be a blind retry, not
genuinely new information.

This is now the **third distinct shard** of the `tradfi-bf-cme-ohlcv-1m-` family to hit this exact
exit_code=137 stall-induced-SIGKILL + relaunch-bound-exhausted shape within a 24h window (`es-2020` and
`g01-6a-6l-2020` on 2026-08-15; `g01-6a-6l-2020` again and now `btc-2020` on 2026-08-16) — a repeating pattern
across DIFFERENT instrument groups (not the same shard recurring, unlike the `g01-6a-6l-2020` same-shard-two-days
case) suggests a launcher-family-wide defect (e.g., an unbounded outbound HTTP call in shared adapter/fetch code
common to the whole `tradfi-bf-cme-ohlcv-1m-` launcher, rather than a per-shard poison instrument) — worth the
operator weighing against the shard-specific hypothesis the `g01-6a-6l-2020` sibling doc raised.

## What this worker did NOT do

- Did not relaunch `tradfi-bf-cme-ohlcv-1m-btc-2020-20260816-180410` or any other `tradfi-bf-cme-ohlcv-1m-` VM.
- Did not pull `run.log` content for this VM (gone from the live fleet; a GCS SDK read of its archived `vm-logs/`
  blob is the next diagnostic step — use
  `deployment_service.data_pipeline_monitors._gcs.read_text`/`read_terminal_exit_code`, never a subprocess
  `gsutil`/`gcloud storage` call, per the workspace GCS-object-ops hard rule — this session's own attempt to even
  LIST a GCS path via subprocess was blocked outright by the `block_destructive_commands.py` guardrail).
- Did not diagnose the in-container stall root cause, and did not cross-check this stall's signature against the
  other three same-family incidents open today/yesterday — that cross-shard signature comparison plus the actual
  root-cause diagnosis is the open work this doc (together with its siblings) tracks.

## Recommended decision (for the operator)

1. Confirm whether the `btc-2020` shard's data (asset_group=tradfi, venue=CME, timeframe=1m OHLCV, instrument=BTC
   futures, year=2020) is still outstanding in the manifest — if genuinely still missing, a relaunch is warranted
   but should wait for either (a) the family's daily `≤2/(vm-prefix,day)` bound to reset, or (b) a root-cause
   diagnosis of the stall first.
2. Given this is now 3 distinct shards of the SAME launcher family stalling within 24h (see "Why this is a PAGE
   case" above), treat this as a candidate launcher-family-wide defect, not three independent flukes — prioritize
   pulling + comparing `run.log` across all four incidents (`es-2020`, `g01-6a-6l-2020`×2, `btc-2020`) to check for
   a shared failure signature (e.g., the same outbound call/venue/timeout site) before assuming per-shard poison
   data.
3. Consider whether the `tradfi-bf-cme-ohlcv-1m-` family's `≤2/(vm-prefix,day)` relaunch bound should temporarily
   tighten to a "diagnose-before-3rd-relaunch-family-wide" gate, given the cross-shard recurrence — a decision for
   the operator, not this worker.

## Todos

- [ ] [OPERATOR] P1. Decide relaunch-vs-wait for `tradfi-bf-cme-ohlcv-1m-btc-2020-20260816-180410`'s shard
      (tradfi/CME/btc/2020 1m OHLCV) per the recommended decision above; the `tradfi-bf-cme-ohlcv-1m-` family
      relaunch bound is already exhausted for today (2/2, per this escalation's own context).
- [ ] [BACKEND] P1. Pull + read `run.log` for all four `tradfi-bf-cme-ohlcv-1m-` DP-VM-001 incidents open
      today/yesterday (`es-2020-20260815-030216`, `g01-6a-6l-2020-20260815-200147`,
      `g01-6a-6l-2020-20260816-162556`, `btc-2020-20260816-180410`) via
      `deployment_service.data_pipeline_monitors._gcs.read_text`/`read_terminal_exit_code` (SDK, never subprocess),
      compare failure signatures across shards, and fix at the root — if it's a shared code defect, bound the
      offending call with `asyncio.wait_for` at the per-shard level per the shard-isolation SSOT; if genuinely
      shard-specific, isolate + skip the poison instrument-date per shard-level failure isolation.

## Progress Log

- 2026-08-16 (slot 1, data_pipeline_failure escalation agt-fc0533): Received escalation for DP-VM-001
  `tradfi-bf-cme-ohlcv-1m-btc-2020-20260816-180410` exit_code=137, flagged by the escalation as stall-induced, not
  OOM. Checked for an existing issue doc naming this VM/shard — none found; found three same-family sibling docs
  (two dated 2026-08-15, one dated today) all at the family's relaunch bound on their respective days. Confirmed
  via `gcloud compute instances list --filter="name~tradfi-bf-cme-ohlcv-1m"` that this exact VM is no longer in the
  live fleet and that the `btc` shard token does not appear anywhere in today's active relaunch wave (which covers
  only `g01`-`g07` groups). Per RB-INFRA-RELAUNCH, did not relaunch. Filed this issue doc, flagging the
  3-distinct-shards-in-24h pattern as a candidate family-wide (not per-shard) defect, and paging the operator via
  `/blocked` per the escalation's explicit instruction. No code changed this session.
