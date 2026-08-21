---
doc_type: issue
title:
  DP-VM-001 exit_code=137 (stall-induced SIGKILL, not OOM) on tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2020-20260815-200147 —
  tradfi-bf-cme-ohlcv-1m- launcher family already at the 2/2 relaunch-dispatch bound today, page instead of relaunch
summary: >-
  A data-pipeline fleet monitor detected VM `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2020-20260815-200147` terminated with
  `exit_code=137` — the escalation's own context flags this as a **stall-induced SIGKILL, not an OOM kill** (137 is the
  raw signal-9 exit code shared by both causes; the dispatching monitor distinguished them and reported this one as
  stall-induced). The `tradfi-bf-cme-ohlcv-1m-` launcher family already used its `≤2/(vm-prefix, day)` RB-INFRA-RELAUNCH
  allowance earlier today (a separate VM in the same family, `tradfi-bf-cme-ohlcv-1m-es-2020-20260815-030216`, was
  already reported at that 2/2 bound and paged via
  `/plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_es_2020_exit137_stall_relaunch_bound_page_2026_08_15.md`). This
  is a DIFFERENT VM/shard (`g01-6a-6l-2020` vs `es-2020`, launched `20260815-200147` vs `20260815-030216`) in the SAME
  launcher family, so the family-level `≤2/(vm-prefix, day)` bound still applies and is still exhausted — a relaunch here
  would be a third same-family blind retry today, not new information. No prior issue doc names this exact VM (grepped
  `plans/active/issues/` for the VM name, the `g01-6a-6l` shard token, and `DP-VM-001`). Confirmed via
  `gcloud compute instances list --filter="name~tradfi-bf-cme-ohlcv-1m"` (0 rows) that this VM is no longer in the live
  fleet — consistent with a terminated/self-deleted VM. This worker did NOT relaunch and did NOT pull `run.log` content
  to diagnose the in-container stall root cause this session — it files this doc and pages the operator per the
  escalation's explicit instruction.
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
    /plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_es_2020_exit137_stall_relaunch_bound_page_2026_08_15.md,
    /plans/archive/issues/tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
context_scope: [/codex/15-runbooks/incidents/rb_infra_relaunch.md, /codex/05-infrastructure/data-pipeline-alerts.md, /plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_20260816_220209_databento_cme_billing_rootcause_2026_08_17.md, deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py, deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py, deployment-service/deployment_service/data_pipeline_monitors/_gcs.py]
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
  Escalation agt-50801c (wall_type=data_pipeline_failure, dispatched to slot 20, 2026-08-15). Context carried the
  finding directly: "VM tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2020-20260815-200147 terminated with exit_code=137
  (stall-induced SIGKILL, not OOM) — captured did not complete cleanly... DO NOT RELAUNCH...
  launcher-family tradfi-bf-cme-ohlcv-1m- already hit 2/2 relaunch dispatches today (RB-INFRA-RELAUNCH bound)." No
  separate audit CSV/candidate list was attached ("Filed issue: (none — alert carries the details)"). VM confirmed
  absent from the live fleet this session (`gcloud compute instances list --filter="name~tradfi-bf-cme-ohlcv-1m"`
  returned zero rows).
---

# DP-VM-001 — tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2020-20260815-200147 exit_code=137 (stall, not OOM), relaunch-bound, page not relaunch

## What happened

- VM: `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2020-20260815-200147` (asset_group=tradfi, launcher-family prefix
  `tradfi-bf-cme-ohlcv-1m-`, shard token `g01-6a-6l-2020` — a batch/group + year shard distinct from the earlier-today
  `es-2020` shard).
- Terminal state: `exit_code=137`, which the dispatching monitor classified as a **stall-induced SIGKILL** (a
  watchdog/heartbeat-timeout kill), not the OOM-killer — a distinction 137 alone can't carry (both share the raw
  signal-9 exit code), but the escalation's context explicitly disambiguates it.
- The `tradfi-bf-cme-ohlcv-1m-` launcher family had already used its `≤2/(vm-prefix, day)` RB-INFRA-RELAUNCH allowance
  today (per this escalation's own context: "already hit 2/2 relaunch dispatches today").
- No issue doc previously named this exact VM. The same-family, same-day sibling incident
  (`dp_vm_001_tradfi_bf_cme_ohlcv_1m_es_2020_exit137_stall_relaunch_bound_page_2026_08_15.md`, escalation agt-4a1f35,
  slot 5, ~03:02 UTC) covers a DIFFERENT VM/shard in the same launcher family — this is a second, distinct occurrence
  of the same failure mode against the same family later the same day (~20:01 UTC), reinforcing that the family-level
  bound is genuinely exhausted rather than a one-off.

## Why this is a PAGE case, not a relaunch

Per `/codex/05-infrastructure/data-pipeline-alerts.md` § "self-heal actuator layer", both `DP_VM_EXIT_NONZERO` (137/OOM,
via `relaunch_backfill_vm.py`) and `DP_VM_STALL`/hung (via `relaunch_stalled_vm.py`) actuators share the identical
`≤2/(vm-prefix, day)` bound. Regardless of which class this finding is (the escalation says stall, not OOM), the family
is already at that bound for today — `RB-INFRA-RELAUNCH`'s own guidance ("if it re-fails the SAME way twice... STOP
relaunching, file an issue") points the same direction: stop and page. The root-cause-diagnosed carve-out (ruled
2026-08-02) does not apply here — no root cause has been diagnosed or fixed this session for either of today's two
`tradfi-bf-cme-ohlcv-1m-` incidents, so a further relaunch would be a third blind retry, not genuinely new information.
Two same-family stalls in one day (a different shard each time) is itself a signal worth the operator's attention —
this could be a systemic issue in the launcher/capture path rather than two unrelated flukes.

## What this worker did NOT do

- Did not relaunch `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2020-20260815-200147` or any other `tradfi-bf-cme-ohlcv-1m-` VM.
- Did not pull `run.log` content for this VM (the VM is gone from the live fleet; a GCS SDK read of its archived
  `vm-logs/` blob is the next diagnostic step for whoever picks this up — use
  `deployment_service.data_pipeline_monitors._gcs.read_text`/`read_terminal_exit_code`, never a subprocess
  `gsutil`/`gcloud storage` call, per the workspace GCS-object-ops hard rule).
- Did not diagnose the in-container stall root cause, and did not cross-check whether this stall shares the same
  signature as the earlier-today `es-2020` stall (candidate causes per the DP-VM-003/stall runbook pattern: an
  unbounded outbound HTTP call lacking `timeout=`, or a per-shard hang in the CME OHLCV 1m capture loop) — that
  cross-check plus the actual root-cause diagnosis is the open work this doc (together with its sibling) tracks.

## Recommended decision (for the operator)

1. Confirm whether the `g01-6a-6l-2020` shard's data is still outstanding (check the manifest for asset_group=tradfi,
   venue=CME, timeframe=1m OHLCV, the instrument set covered by group `g01` chains `6a`-`6l`, year=2020) — if
   genuinely still missing, a relaunch is warranted but should wait for either (a) the family's daily
   `≤2/(vm-prefix,day)` bound to reset, or (b) a root-cause diagnosis of the stall first (the root-cause-diagnosed
   carve-out in `RB-INFRA-RELAUNCH`).
2. Pull `run.log` for BOTH today's `tradfi-bf-cme-ohlcv-1m-` stalls (`es-2020-20260815-030216` and
   `g01-6a-6l-2020-20260815-200147`) via the SDK helpers above and compare failure signatures — two stalls in the same
   family in one day warrants checking whether this is one systemic defect (e.g. a shared unbounded HTTP call in the
   CME OHLCV 1m capture path) rather than two independent incidents.

## Todos

> **CORRECTED 2026-08-18 (plan_reconciler)**: both todos below are stale — this exact VM/shard is now confirmed
> **billing-caused**, not an independent relaunch-vs-wait or shared-code-defect question. See
> `dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_20260816_220209_databento_cme_billing_rootcause_2026_08_17.md`
> (root cause: tracked Databento CME billing block). Once billing is restored, this shard needs a fresh relaunch —
> the family's normal backfill-completion sweep will pick it up, not urgent to track separately here (same
> disposition as the sibling `btc-2020`/`es-2020` docs already record).

- [x] ✅ [OPERATOR] P1. **CLOSED 2026-08-21 (na-eligibility-audit, tradfi tranche) — moot, per the 2026-08-18 correction
      above.** Decide relaunch-vs-wait for `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2020-20260815-200147`'s shard
      (tradfi/CME/g01-6a-6l/2020 1m OHLCV); the `tradfi-bf-cme-ohlcv-1m-` family relaunch bound is already exhausted for
      today (2/2, per this escalation's own context). SUPERSEDED — see correction above: the root cause is the
      already-tracked Databento CME billing block
      (`dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_20260816_220209_databento_cme_billing_rootcause_2026_08_17.md`,
      `tradfi_databento_account_billing_suspended_2026_08_09.md`), not an independent per-shard relaunch decision; once
      billing clears, the family's normal backfill-completion sweep picks this shard up, no separate operator action
      needed here.
- [x] ✅ [BACKEND] P2. **CLOSED 2026-08-21 (na-eligibility-audit, tradfi tranche) — moot, per the 2026-08-18 correction
      above.** Pull + read `run.log` for both `tradfi-bf-cme-ohlcv-1m-es-2020-20260815-030216` and
      `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2020-20260815-200147` via
      `deployment_service.data_pipeline_monitors._gcs.read_text`/`read_terminal_exit_code` (SDK, never subprocess),
      compare failure signatures, and fix at the root if it's a shared code defect. SUPERSEDED — see correction above:
      the `g01-6a-6l-2020` shard's failure signature is confirmed billing-caused (402 `account_delinquent_invoice`),
      not a shared code defect needing an `asyncio.wait_for` bound; the sibling `es-2020` shard's own run.log pull was
      separately consolidated into `tradfi_satellite_ao_dispatch_batch15_2026_08_17.md` Todo 2 (confirmed genuine
      `WORKER_STALLED`, unrelated cause) — no further diagnostic action needed on either shard from this doc.

## Progress Log

- 2026-08-15 (slot 20, data_pipeline_failure escalation agt-50801c): Received escalation for DP-VM-001
  `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2020-20260815-200147` exit_code=137, flagged by the escalation as stall-induced, not
  OOM. Checked for an existing issue doc naming this VM — none found; found the same-day, same-family sibling doc for a
  different shard (`es-2020-20260815-030216`, escalation agt-4a1f35, slot 5) already at the family's 2/2 relaunch bound.
  Confirmed via `gcloud compute instances list --filter="name~tradfi-bf-cme-ohlcv-1m"` the VM is no longer in the live
  fleet (0 rows). Per RB-INFRA-RELAUNCH, both the OOM and stall actuator classes share the identical
  `≤2/(vm-prefix, day)` bound, and the family was already reported at that bound today — did not relaunch. Filed this
  issue doc and paging the operator via `/blocked` per the escalation's explicit instruction. **na-eligibility-audit 2026-08-16** (tradfi tranche, dispatch agt-45ad7b): **KEEP-NA, valid.** Todo 1 is an explicit
[OPERATOR] relaunch-vs-wait judgment call. Genuinely operator-gated. assigned_vm unchanged. No code changed this
  session.
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
- **na-eligibility-audit 2026-08-18** (tradfi tranche, dispatch agt-31bfcb): **KEEP-NA, valid.** Both open todos
  confirmed SUPERSEDED by plan_reconciler's same-day correction (billing-caused, see
  `dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_20260816_220209_databento_cme_billing_rootcause_2026_08_17.md`) —
  correctly left unflipped pending the family's normal relaunch sweep once billing clears (not a fresh RECLASSIFY
  candidate; nothing dispatchable right now). `assigned_vm` unchanged.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-21** (tradfi tranche): **ARCHIVE.** Both todos closed above (moot, per the
  2026-08-18 plan_reconciler correction — this shard's failure is the already-tracked Databento CME billing block,
  fully covered elsewhere; the sibling `es-2020` run.log pull already landed via batch15). 0 open todos, unlocked
  (`locked_by:` empty). Matches `ag_closeout_audit_tradfi_parked_2026_08_19.md`'s independent `archivable_now`
  classification. `status: resolved`; archived to `plans/archive/issues/` this pass, referrers swept.
