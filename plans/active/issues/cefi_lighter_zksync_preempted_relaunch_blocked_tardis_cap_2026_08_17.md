---
doc_type: issue
title: "cefi-lighter-zksync-2026 preempted backfill VM can't auto-relaunch — Tardis cap-1 occupied, page-once suppression means no automatic retry once it clears"
summary: >-
  DP-VM-008 escalation (agt-861d79) for VM `cefi-lighter-zksync-2026-20260817-010152` (SPOT-preempted, ~79% done —
  chunk 182/229, `PROGRESS.json` `last_completed_date=2026-07-02`, `monotonic=true`). The in-band `RelaunchPreemptedVm`
  auto-recover actuator already attempted this and self-paged `DP_VM_PREEMPTED_NO_RELAUNCH` (durably suppressed for
  this exact `vm_name` per its page-once-per-VM-name design). Root cause confirmed via a manual repro against the LIVE
  guard: `tardis_running_vm_count` (the guard's own function, sourced directly) returns 1 right now —
  `cefi-binance-futures-2026-heavy-20260817-010713` holds the single Tardis-cap-1 slot (BINANCE-FUTURES is not
  cap-exempt; LIGHTER-ZKSYNC is not cap-exempt either — its `derivative_ticker` leg has no native-REST source, Tardis
  only, per `tardis-concurrency-guard.sh`'s own header). The holder is actively progressing (heartbeat/run.log ~2min
  fresh) but only at `last_completed_date=2026-06-03` of a `heavy` multi-year scope — not close to finishing, so this
  is not a short wait. No live replacement VM exists for the `cefi-lighter-zksync` prefix (checked
  `gcloud compute instances list --filter="name~'^cefi-lighter-zksync'"` — empty). Declining to `FORCE=1` past the
  cap — that overrides a HARD RULE (operator, 2026-07-16, `tardis-concurrency-guard.sh`) that exists specifically to
  prevent a measured mutual-403 storm (+37,212 FALSE `attempted_failed` rows in one 2026-07-16 incident) — this is
  routine INFO-severity SPOT churn with a safe, monotonic checkpoint, not a case that justifies the override. This is
  the SAME operating pattern already established for the `cefi-queue-heavy-binancefutu-x17` chain in
  `cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md` (decline + wait when the cap is occupied by another
  VM, relaunch once clear) — not a novel bug, and the `data_pipeline_alert_storm_root_cause_batch_2026_08_10.md` fix
  (durable per-VM GCS claim state) already closed the REPEATED-paging class this doc's storm was about. The residual
  gap this doc DOES surface: once `_already_paged` is set for a `vm_name`, NOTHING re-checks the Tardis cap later and
  retries automatically when it frees — the retry is durably handed to a human/AO-dispatched worker with no standing
  mechanism watching for "cap now clear, and there's a paged-but-never-relaunched VM waiting."
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [deployment-service]
scope: [engineer, admin]
tags: [cefi, tardis, vm-preemption, dp-vm-008, dp-vm-009, relaunch, cap-1, big-finding]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /plans/active/issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md,
    /plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md,
  ]
parent_epic: cefi_master
source: "DP-VM-008 escalation agt-861d79 (data_pipeline_failure worker, slot 7), 2026-08-17"
assigned_vm: planning
resolved_by:
locked_by:
locked_since:
priority: P2
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
created: 2026-08-17
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh,
    deployment-service/scripts/vm/tardis-concurrency-guard.sh,
    deployment-service/scripts/recovery/relaunch_backfill_vm.py,
  ]
---

# cefi-lighter-zksync-2026 preempted backfill blocked on Tardis cap-1 — relaunch deferred, not lost

## What I found

Escalation `agt-861d79` dispatched me to relaunch `cefi-lighter-zksync-2026-20260817-010152` (SPOT-preempted). Read
its durable state before acting:

- `LAUNCH_PARAMS.json` env: `VENUES`, `SYMBOLS`, `DATA_TYPES`, `OVERRIDE_START_DATE`, `OVERRIDE_END_DATE`, `FORCE`
  (captured verbatim, not re-derived).
- `PROGRESS.json`: `{"last_completed_date": "2026-07-02", "monotonic": true, "updated": "2026-08-17T03:37:59Z"}` — a
  safe, monotonic resume point. `run.log` shows `chunk=182/229` at the moment of preemption (~79% through this
  shard's chunk range).
- `vm-census/relaunch-paged/vm/cefi-lighter-zksync-2026-20260817-010152.json` **exists** — the in-band actuator
  (`RelaunchPreemptedVm`) already tried and self-paged `DP_VM_PREEMPTED_NO_RELAUNCH` (CRITICAL, `#data-pipeline-alerts`
  `ts=1786939316.418119`). Per its own design this is a durable, page-ONCE-per-`vm_name` suppression — no future
  automated sweep will ever retry this exact VM name again.
- No live replacement: `gcloud compute instances list --filter="name~'^cefi-lighter-zksync'"` → empty.
- No supervising wrapper covers this shard: `rotate-cefi-backfill-vm.sh` only supervises the DIFFERENT
  `cefi-queue-*` naming convention (a distinct launch mode), not `cefi-lighter-zksync-*`.

**Root cause, confirmed live** (sourced `tardis-concurrency-guard.sh` directly and called its own
`tardis_running_vm_count asia-northeast1-c central-element-323112`): returns `1`. The live fleet shows
`cefi-binance-futures-2026-heavy-20260817-010713` RUNNING — BINANCE-FUTURES is not in `TARDIS_CAP_EXEMPT_VENUES`
(`HYPERLIQUID ASTER EXTENDED-STARKNET COINBASE-CDE`), so it holds the single Tardis-cap-1 slot. LIGHTER-ZKSYNC is
ALSO not cap-exempt (removed from the exemption list 2026-07-30 — its `derivative_ticker` leg has no native-REST
source, Tardis-only). A relaunch attempt right now (`1 running + 1 planned = 2 > cap 1`) would be REFUSED by
`tardis_guard_reserve_slot` — exactly the outcome the already-paged `DP_VM_PREEMPTED_NO_RELAUNCH` almost certainly
recorded (guard refusal is one of `RelaunchPreemptedVm`'s explicit page-triggering failure paths).

Checked whether the holder is close to freeing the slot: its own `PROGRESS.json` shows `last_completed_date=2026-06-03`
against a `heavy` multi-year scope, with a fresh heartbeat/run.log (~2min old — genuinely progressing, not stuck) —
this is a long-running shard, not a near-term completion. Waiting it out is not feasible within a one-shot escalation
worker's liveness window.

## Why I did not force it

`FORCE=1` bypasses the Tardis cap-1 HARD RULE (operator, 2026-07-16) that exists specifically because N>1 measured a
mutual-403 storm in production (2026-07-16: 10,300×403/912 ok on one VM, 15,034×403/0 ok on another, +37,212 FALSE
`attempted_failed` rows in 8h, coverage went BACKWARD). This is routine INFO-severity SPOT churn with a clean,
monotonic checkpoint and no urgency — not the kind of case the doc's own precedent (`cefi_track2_backfill_vm_
preempted_no_recovery_2026_07_30.md`, todo dated 2026-08-06) used to justify its one recorded FORCE=1 override (an
explicit operator ruling after a MUCH longer stuck chain). Declining to relaunch now and recording the exact recipe
for later is the same posture ~10 independent review-craft dispatches took in that doc when they found the cap
occupied — decline, log, do not hold the slot for a multi-day-scale wait.

## The residual gap (separate from this one VM)

Once `_already_paged` is set, the automated path for that `vm_name` is closed forever, but nothing else watches for
"the Tardis slot has since freed, and there's a paged-but-never-relaunched VM waiting." Today the recovery is
100% human/AO-worker-driven from the Slack page (which is the runbook's designed behavior, not a bug) — but there is
no standing reconciler that would notice this VM SPECIFICALLY needs attention once
`cefi-binance-futures-2026-heavy-20260817-010713` (or its eventual successor) finishes or gets preempted itself.
Given the docs already list a 414-message `DP_VM_PREEMPTED_NO_RELAUNCH` volume in the last 30h
(`#data-pipeline-alerts`, checked 2026-08-17), most of that volume is plausibly this SAME class (Tardis cap-1
contention across many shards, each paging once, by design) rather than a bug — but nobody has verified that at
scale. Filing this as P2 (not a fix I have — a genuine design question: should there be a periodic "check the cap,
retry the oldest paged-but-not-relaunched VM" reconciler, or is human-driven retry-on-page the intended steady
state at current preemption volume?).

## Recommended decision

- **A [RECOMMENDED]**: Once the Tardis cap frees (`tardis_running_vm_count` returns 0), relaunch
  `cefi-lighter-zksync-2026` reproducing the captured `LAUNCH_PARAMS.json` env verbatim
  (`VENUES`/`SYMBOLS`/`DATA_TYPES`/`OVERRIDE_START_DATE`/`OVERRIDE_END_DATE`/`FORCE` — read fresh from
  `gs://deployment-scripts-central-element-323112/vm-logs/cefi-lighter-zksync-2026-20260817-010152/LAUNCH_PARAMS.json`
  at relaunch time, don't hand-copy this doc's snapshot) via `launch-cefi-sharded-backfill.sh`, with `START_DATE`
  overridden to the checkpoint frontier (`2026-07-02`) per the standard preemption-recovery contract
  (`spot-vms-for-backfill.md` § "Preemption recovery MUST resume from PROGRESS"). Verify STARTED@T+60s + PROGRESS@T+10min,
  per the no-fire-and-forget rule.
- **B**: Assess (as a separate, small design todo) whether a periodic cap-aware reconciler for
  `DP_VM_PREEMPTED_NO_RELAUNCH`-paged VMs is worth building, or whether the current volume is low enough that
  human/AO-worker-driven retry-on-page is fine as the steady state.

## Todos

- [ ] [INFRA] P2. Once `tardis_running_vm_count asia-northeast1-c central-element-323112` (source
      `deployment-service/scripts/vm/tardis-concurrency-guard.sh`) returns `0`, relaunch
      `cefi-lighter-zksync-2026` per option A above. Verify STARTED@T+60s + PROGRESS@T+10min before closing this
      todo. Repo: deployment-service.
- [ ] [DATA] P3. Sample ~20 of the 414 `DP_VM_PREEMPTED_NO_RELAUNCH` messages posted to `#data-pipeline-alerts` in the
      last 30h (as of 2026-08-17) and classify each by failure reason (Tardis cap-1 guard refusal vs. something else)
      to confirm/refute that this is the dominant class at current volume — informs whether option B (a cap-aware
      reconciler) is worth building. Repo: unified-trading-pm (analysis-only, no code).

## Progress Log

- 2026-08-17 — Filed by DP-VM-008 escalation worker (slot 7, agt-861d79). Diagnosed root cause (Tardis cap-1 occupied
  by `cefi-binance-futures-2026-heavy-20260817-010713`, confirmed live via the guard's own `tardis_running_vm_count`
  function), confirmed no safe near-term path to complete the relaunch this session, declined to `FORCE=1` past the
  hard cap rule, and captured the exact recipe (launch_env + checkpoint) for the next worker. `AUTHORING_SLOT` was
  `dp-fleet-monitor` (non-numeric) — skipped the authoring-slot ping per the runbook's documented carve-out (the
  dispatch-time Slack alert already covers the FYI).
