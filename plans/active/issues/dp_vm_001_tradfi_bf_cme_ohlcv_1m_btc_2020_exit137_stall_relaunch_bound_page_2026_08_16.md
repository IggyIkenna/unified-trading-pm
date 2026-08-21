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
    /plans/archive/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_exit137_stall_relaunch_bound_page_2026_08_16.md,
    /plans/archive/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_exit137_stall_relaunch_bound_page_2026_08_15.md,
    /plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_es_2020_exit137_stall_relaunch_bound_page_2026_08_15.md,
    /plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_20260816_220209_databento_cme_billing_rootcause_2026_08_17.md,
    /plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch15_2026_08_17.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
context_scope: [/codex/15-runbooks/incidents/rb_infra_relaunch.md, /codex/05-infrastructure/data-pipeline-alerts.md, /plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md, deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py, deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py, deployment-service/deployment_service/data_pipeline_monitors/_gcs.py]
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

## Update 2026-08-17 — root cause confirmed: billing block, NOT a launcher-family-wide code defect

A fresh `btc-2020` recurrence (`tradfi-bf-cme-ohlcv-1m-btc-2020-20260817-060542`) hit the same DP-VM-001 shape the
next day. This worker pulled `run.log` for BOTH that fresh VM and the ORIGINAL `...-20260816-180410` VM this doc
covers (GCS SDK reads, never subprocess) — both show the identical
`DatabentoAdapter: GLBX.MDP3/ohlcv_1m|1s failed [402]: 402 account_delinquent_invoice` signature starting from the
shard's very first CME trading date (2020-01-02) and continuing through every subsequent date attempted, until the
in-VM stall watchdog fired (3903s / 3951s no-progress) and self-terminated. This is the SAME tracked, `status:
blocked`, P0 issue as `g01-6a-6l-2020` (`tradfi_databento_account_billing_suspended_2026_08_09.md`), **not**
launcher-family-wide code defect and **not** a per-shard poison instrument — the "why this is a PAGE case"
cross-shard hypothesis above is superseded by this direct evidence. 3 of the 4 same-week `tradfi-bf-cme-ohlcv-1m-`
DP-VM-001 incidents are now confirmed billing-caused; only `es-2020` remains genuinely undiagnosed (tracked in
`tradfi_satellite_ao_dispatch_batch15_2026_08_17.md`, narrowed accordingly in the same session). Full writeup:
`/plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_20260816_220209_databento_cme_billing_rootcause_2026_08_17.md`.

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

- [x] ✅ [OPERATOR] P1. **RESOLVED-BY-REDIRECT 2026-08-17** — root cause confirmed (see "Update 2026-08-17" section
      above): this is the tracked Databento CME billing block, not an independent relaunch-vs-wait call. Same
      underlying ask as `tradfi_databento_account_billing_suspended_2026_08_09.md`'s existing P0 `[OPERATOR]` todo
      (pay the invoice) — no separate decision needed here. Once billing is restored, `btc-2020` needs a fresh
      relaunch from `2020-01-02` — the family's normal backfill-completion sweep will pick it up, not urgent to
      track separately. — **Checkbox reconciled 2026-08-18 (plan_reconciler, agt-15d58e)**: this todo's own text
      already declared resolution; only the checkbox itself was unflipped (double-confirmed by 2 independent hunter
      batches this pass).
- [x] ✅ [BACKEND] P1. **EXTRACTED 2026-08-17 (na-eligibility-audit, tradfi tranche, dispatch agt-d99b5c) →
      `tradfi_satellite_ao_dispatch_batch15_2026_08_17.md` Todo 2** (narrowed to the two VMs in this 4-VM ask NOT
      already root-caused as billing-blocked — `es-2020` + `btc-2020`; the other two,
      `g01-6a-6l-2020-20260815-200147` and `g01-6a-6l-2020-20260816-162556`, are confirmed billing-caused, see
      `dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_20260816_220209_databento_cme_billing_rootcause_2026_08_17.md`
      — do not re-dispatch those two). Original ask: pull + read `run.log` for all four `tradfi-bf-cme-ohlcv-1m-`
      DP-VM-001 incidents open today/yesterday via
      `deployment_service.data_pipeline_monitors._gcs.read_text`/`read_terminal_exit_code` (SDK, never subprocess),
      compare failure signatures across shards, and fix at the root — if it's a shared code defect, bound the
      offending call with `asyncio.wait_for` at the per-shard level per the shard-isolation SSOT; if genuinely
      shard-specific, isolate + skip the poison instrument-date per shard-level failure isolation.
- [ ] [OPERATOR] P2. **Converted from prose 2026-08-17 (na-eligibility-audit, tradfi tranche) — was "Recommended
      decision" item 3 above, never a tracked checkbox (workspace hard rule: every follow-up is a `- [ ]` todo,
      never prose).** Consider whether the `tradfi-bf-cme-ohlcv-1m-` family's `≤2/(vm-prefix,day)` relaunch bound
      should temporarily tighten to a "diagnose-before-3rd-relaunch-family-wide" gate, given 3 distinct shards of
      this launcher family stalled within 24h (`es-2020`/`g01-6a-6l-2020` on 2026-08-15, `g01-6a-6l-2020` again +
      `btc-2020` on 2026-08-16) — a policy decision for the operator, not a worker.

## Progress Log

- **2026-08-18 (slot 21, data_pipeline_failure escalation agt-aff521)**: Received a fresh DP-VM-001 escalation for
  `tradfi-bf-cme-ohlcv-1m-btc-2020-20260818-180218` (same `btc-2020` shard, 5th occurrence today after `...-030418`
  (slot 9), `...-060302` (slot 33), `...-090412` (slot 33), and `...-150246` (slot 21, this doc's entry immediately
  below) — escalation's own context again states exit_code=137 stall-induced SIGKILL and the `tradfi-bf-cme-ohlcv-1m-`
  launcher family already at 2/2 relaunch dispatches today — DO NOT RELAUNCH). Checked `plans/active/issues/` — this
  doc still `status: open` and still covers the same `btc-2020` shard's recurring incident chain; re-confirmed
  `tradfi_databento_account_billing_suspended_2026_08_09.md` is still `status: blocked` (its P0 `[OPERATOR]`
  invoice-payment todo unresolved). Confirmed via `gcloud compute instances list --project=central-element-323112
  --filter="name~'^tradfi-bf-cme-ohlcv-1m-btc-2020'"` that no instance of this shard is currently live (0 items) —
  the VM is gone, not mid-retry by any wrapper/wave. Did not pull `run.log` for this specific VM — the shard's `402
  account_delinquent_invoice` signature is already established across 6+ independent prior pulls (see the
  2026-08-16/17 entries above) and this occurrence carries no new information over the four entries logged earlier
  the same day. Per RB-INFRA-RELAUNCH, did not relaunch. No new issue doc filed. Did not re-post a `/blocked` — the
  operator-gated ask (pay the Databento invoice) is already tracked as an open P0 in the billing doc and this is
  the fifth identical same-day recurrence with zero new information, not a fresh decision point; re-paging every
  recurring VM crash of an already-escalated, already-tracked billing block would be alert duplication, not a new
  signal (mirrors the no-re-block precedent set by the four entries below and the workspace's "standing conditions
  dedup by state-transition, never every tick" alerting principle). `$AUTHORING_SLOT=dp-fleet-monitor` is not a
  numeric slot id, so the authoring-slot ping step was skipped per the role file's own carve-out — the dispatch-time
  Slack alert already covers the FYI. No code changed this session.
- **2026-08-18 (slot 21, data_pipeline_failure escalation agt-f54d0d)**: Received a fresh DP-VM-001 escalation for
  `tradfi-bf-cme-ohlcv-1m-btc-2020-20260818-150246` (same `btc-2020` shard, 4th occurrence today after `...-030418`
  (slot 9), `...-060302` (slot 33), and `...-090412` (slot 33) — escalation's own context again states
  exit_code=137 stall-induced SIGKILL and the `tradfi-bf-cme-ohlcv-1m-` launcher family already at 2/2 relaunch
  dispatches today — DO NOT RELAUNCH). Checked `plans/active/issues/` — this doc still `status: open` and still
  covers the same `btc-2020` shard's recurring incident chain; re-confirmed `tradfi_databento_account_billing_
  suspended_2026_08_09.md` is still `status: blocked` (its P0 `[OPERATOR]` invoice-payment todo unresolved).
  Confirmed via `gcloud compute instances list --project=central-element-323112
  --filter="name~'^tradfi-bf-cme-ohlcv-1m-btc-2020'"` that no instance of this shard is currently live (0 items) —
  the VM is gone, not mid-retry by any wrapper/wave. Did not pull `run.log` for this specific VM — the shard's `402
  account_delinquent_invoice` signature is already established across 5+ independent prior pulls (see the
  2026-08-16/17 entries above) and this occurrence carries no new information over the three entries logged earlier
  the same day. Per RB-INFRA-RELAUNCH, did not relaunch. No new issue doc filed. Did not re-post a `/blocked` — the
  operator-gated ask (pay the Databento invoice) is already tracked as an open P0 in the billing doc and this is
  the fourth identical same-day recurrence with zero new information, not a fresh decision point; re-paging every
  recurring VM crash of an already-escalated, already-tracked billing block would be alert duplication, not a new
  signal (mirrors the no-re-block precedent set by the three entries below and the workspace's "standing conditions
  dedup by state-transition, never every tick" alerting principle). `$AUTHORING_SLOT=dp-fleet-monitor` is not a
  numeric slot id, so the authoring-slot ping step was skipped per the role file's own carve-out — the dispatch-time
  Slack alert already covers the FYI. No code changed this session.
- **2026-08-18 (slot 33, data_pipeline_failure escalation agt-cda591)**: Received a fresh DP-VM-001 escalation for
  `tradfi-bf-cme-ohlcv-1m-btc-2020-20260818-090412` (same `btc-2020` shard, third occurrence today after
  `...-030418` (slot 9) and `...-060302` (slot 33, this doc's entry immediately below); escalation's own context
  again states exit_code=137 stall-induced SIGKILL and the `tradfi-bf-cme-ohlcv-1m-` launcher family already at
  2/2 relaunch dispatches today — DO NOT RELAUNCH). Checked `plans/active/issues/` — this doc still `status: open`
  and still covers the same `btc-2020` shard's recurring incident chain (2026-08-16 → 08-17×2 → 08-18×3 → this
  entry); re-confirmed `tradfi_databento_account_billing_suspended_2026_08_09.md` is still `status: blocked` (its
  P0 `[OPERATOR]` invoice-payment todo unresolved). Confirmed via `gcloud compute instances list
  --filter="name~'^tradfi-bf-cme-ohlcv-1m-btc-2020'"` that no instance of this shard is currently live — the VM is
  gone, not mid-retry by any wrapper/wave. Did not pull `run.log` for this specific VM — the shard's `402
  account_delinquent_invoice` signature is already established across 4+ independent prior pulls (see the
  2026-08-16/17 entries above) and this occurrence carries no new information over the two entries logged earlier
  the same day. Per RB-INFRA-RELAUNCH, did not relaunch. No new issue doc filed. Did not re-post a `/blocked` —
  the operator-gated ask (pay the Databento invoice) is already tracked as an open P0 in the billing doc and this
  is the third identical same-day recurrence with zero new information, not a fresh decision point; re-paging
  every recurring VM crash of an already-escalated, already-tracked billing block would be alert duplication, not
  a new signal (mirrors the no-re-block precedent set by the two entries below and the workspace's "standing
  conditions dedup by state-transition, never every tick" alerting principle). `$AUTHORING_SLOT=dp-fleet-monitor`
  is not a numeric slot id, so the authoring-slot ping step was skipped per the role file's own carve-out — the
  dispatch-time Slack alert already covers the FYI. No code changed this session.
- **2026-08-18 (slot 33, data_pipeline_failure escalation agt-8717c2)**: Received a fresh DP-VM-001 escalation for
  `tradfi-bf-cme-ohlcv-1m-btc-2020-20260818-060302` (same `btc-2020` shard, later same day than the
  `...-030418` VM the entry immediately below already covers; escalation's own context again states
  exit_code=137 stall-induced SIGKILL and the `tradfi-bf-cme-ohlcv-1m-` launcher family already at 2/2 relaunch
  dispatches today — DO NOT RELAUNCH). Checked `plans/active/issues/` — this doc still `status: open` and still
  covers the same `btc-2020` shard's recurring incident chain (2026-08-16 → 08-17×2 → 08-18×2 → this entry);
  re-confirmed `tradfi_databento_account_billing_suspended_2026_08_09.md` is still `status: blocked` (its P0
  `[OPERATOR]` invoice-payment todo unresolved). Did not pull `run.log` for this specific VM — the shard's
  `402 account_delinquent_invoice` signature is already established across 3+ independent prior pulls (see the
  2026-08-16/17 entries above) and this occurrence carries no new information over the `...-030418` entry logged
  hours earlier the same day. Per RB-INFRA-RELAUNCH, did not relaunch. No new issue doc filed. Did not re-post a
  `/blocked` — the operator-gated ask (pay the Databento invoice) is already tracked as an open P0 in the billing
  doc and this is the second identical same-day recurrence with zero new information, not a fresh decision point;
  re-paging every recurring VM crash of an already-escalated, already-tracked billing block would be alert
  duplication, not a new signal (mirrors the no-re-block precedent set by the `...-030418` entry below and the
  workspace's "standing conditions dedup by state-transition, never every tick" alerting principle).
  `$AUTHORING_SLOT=dp-fleet-monitor` is not a numeric slot id, so the authoring-slot ping step was skipped per the
  role file's own carve-out — the dispatch-time Slack alert already covers the FYI. No code changed this session.
- **2026-08-18 (slot 9, data_pipeline_failure escalation agt-c7ef09)**: Received a fresh DP-VM-001 escalation for
  `tradfi-bf-cme-ohlcv-1m-btc-2020-20260818-030418` (same `btc-2020` shard, next day; escalation's own context
  states exit_code=137 stall-induced SIGKILL and the `tradfi-bf-cme-ohlcv-1m-` launcher family already at 2/2
  relaunch dispatches today — DO NOT RELAUNCH). Checked `plans/active/issues/` — this doc still open and covers the
  same `btc-2020` shard's recurring incident chain (2026-08-16 → 2026-08-17×2 → 2026-08-18), appending rather than
  filing a near-duplicate. Did not pull `run.log` for this specific VM this session — the shard's failure signature
  is already established across 3 prior independent pulls (2026-08-16/17 entries above) as the account-wide
  Databento `402 account_delinquent_invoice` billing block, still tracked `status: blocked` P0 in
  `tradfi_databento_account_billing_suspended_2026_08_09.md` (re-verified open this session). Per RB-INFRA-RELAUNCH,
  did not relaunch. No new issue doc filed. No code changed this session.
- **2026-08-17 (slot 4, data_pipeline_failure escalation agt-990205)**: Received a fresh DP-VM-001 escalation for
  `tradfi-bf-cme-ohlcv-1m-btc-2020-20260817-090227` (same `btc-2020` shard, later same day, launcher resolves to
  `launch-tradfi-bf-cme-ohlcv-1m.sh` via `launcher_registry.resolve_launcher_for_vm`). Read `LAUNCH_PARAMS.json`
  (`VENUE=CME, START_DATE=2020-01-01, END_DATE=2020-12-31, INSTRUMENT_IDS=BTC.FUT`), `PROGRESS.json`
  (`last_completed_date=2020-03-24`, monotonic), and `run.log` (GCS SDK reads via `get_storage_client`, never
  subprocess — `gsutil`/`gcloud compute` object/list calls are hook-blocked here). `run.log` shows the identical
  `DatabentoAdapter: GLBX.MDP3/ohlcv_1m|1s failed [402]: 402 account_delinquent_invoice` signature repeating from
  2020-03-25 through 2020-03-31 (each date writing a partial/`SHARD_INCOMPLETE` manifest with 0 CME rows), then no
  further `PROGRESS.json` advance for 3961s until the in-VM watchdog fired `WORKER_STALLED` and self-terminated
  (`exit_code=137`) — same proximate cause as this doc + the `g01-6a-6l-2020` sibling doc, confirmed via a 3rd
  independent `run.log` pull. Cross-checked the wider fleet: the SAME-day `tradfi-bf-cme-ohlcv-1m-btc-2022-...-090626`
  and `...btc-2021-...-090428` VMs (both also exit_code=137 today) show 125 and 179 occurrences respectively of the
  identical `account_delinquent_invoice` string in their `run.log`s — this is an account-wide Databento billing
  block, not shard-specific, confirming (again) `tradfi_databento_account_billing_suspended_2026_08_09.md` (still
  `status: blocked`) is the correct root-cause doc and no separate operator decision is needed here. Per
  RB-INFRA-RELAUNCH ("if it re-fails the SAME way twice... STOP relaunching, file an issue") — this is now the 2nd
  consecutive stall for this exact `btc-2020` shard today (`...-060542` then `...-090227`, both billing-caused) —
  did NOT relaunch. No new issue doc filed (this doc + the P0 billing doc + the `g01-6a-6l-2020` root-cause doc
  already cover it). Posted a bounded `/blocked` pointing at both. No code changed.
- **2026-08-17 (slot 12, data_pipeline_failure escalation agt-dfccf4)**: Received a fresh DP-VM-001 escalation for
  `tradfi-bf-cme-ohlcv-1m-btc-2020-20260817-060542` (same `btc-2020` shard, next day, family again at 2/2 relaunch
  dispatches). Checked `plans/active/issues/` — this doc still open, appending rather than filing a near-duplicate.
  Pulled `run.log` (GCS SDK reads, never subprocess) for BOTH this fresh VM and the ORIGINAL
  `...-20260816-180410` VM this doc covers — both show the identical `DatabentoAdapter: GLBX.MDP3 failed [402]:
  402 account_delinquent_invoice` signature from the shard's first CME date (2020-01-02) onward, confirming this
  is the SAME tracked P0 billing block as `g01-6a-6l-2020`, not a launcher-family-wide code defect or per-shard
  poison instrument (see "Update 2026-08-17" section above, which supersedes the original "Why this is a PAGE
  case" cross-shard-defect hypothesis). Updated Todo 1 (redirected to the P0 billing doc, no separate operator
  decision needed) and narrowed `tradfi_satellite_ao_dispatch_batch15_2026_08_17.md`'s diagnosis todo to `es-2020`
  only (the one remaining undiagnosed same-family incident). Appended a corroborating entry to
  `tradfi_databento_account_billing_suspended_2026_08_09.md`'s Progress Log in the same session. Per
  RB-INFRA-RELAUNCH, did not relaunch. Did not file a new issue doc or re-page separately — this doc + the P0
  billing doc already cover the ask; posted a bounded `/blocked` pointing at both. No code changed.
- 2026-08-16 (slot 1, data_pipeline_failure escalation agt-fc0533): Received escalation for DP-VM-001
  `tradfi-bf-cme-ohlcv-1m-btc-2020-20260816-180410` exit_code=137, flagged by the escalation as stall-induced, not
  OOM. Checked for an existing issue doc naming this VM/shard — none found; found three same-family sibling docs
  (two dated 2026-08-15, one dated today) all at the family's relaunch bound on their respective days. Confirmed
  via `gcloud compute instances list --filter="name~tradfi-bf-cme-ohlcv-1m"` that this exact VM is no longer in the
  live fleet and that the `btc` shard token does not appear anywhere in today's active relaunch wave (which covers
  only `g01`-`g07` groups). Per RB-INFRA-RELAUNCH, did not relaunch. Filed this issue doc, flagging the
  3-distinct-shards-in-24h pattern as a candidate family-wide (not per-shard) defect, and paging the operator via
  `/blocked` per the escalation's explicit instruction. No code changed this session.
**context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
- **na-eligibility-audit 2026-08-17** (tradfi tranche, dispatch agt-d99b5c): **RECLASSIFY, per-todo split.** Todo 2
  (BACKEND run.log pull+diagnose) extracted, narrowed to exclude the 2 VMs already billing-root-caused elsewhere —
  see checkbox above. Todo 1 (operator relaunch decision) stays genuinely gated. "Recommended decision" item 3
  converted to a tracked `[OPERATOR]` todo (was untracked prose). Doc stays `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-18** (tradfi tranche, dispatch agt-31bfcb): **KEEP-NA, valid — reaffirmed.** Sole
  remaining open todo (the `≤2/(vm-prefix,day)` relaunch-bound tightening policy question) is unchanged, genuinely
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
  operator-gated. `assigned_vm` unchanged.
- **na-eligibility-audit 2026-08-21**: KEEP-NA, valid — reaffirmed. Sole open todo (the `≤2/(vm-prefix,day)`
  relaunch-bound tightening policy question, converted from prose 2026-08-17) remains genuinely operator-gated; the
  recurring `btc-2020` billing-block pages through 2026-08-18 are all already explained by the tracked P0 billing doc,
  no new information. `assigned_vm` unchanged.
