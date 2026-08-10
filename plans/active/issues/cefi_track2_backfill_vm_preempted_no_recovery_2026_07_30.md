---
doc_type: issue
title: CeFi Track-2 coverage backfill VM preempted 2026-07-28, never recovered — finalize chain blocked
summary: >-
  Investigating the finalize-001 task (Reconcile CeFi Track-2 checkboxes) found the gating plan's own gate is NOT
  actually satisfied — only 3 of 5 todos in cefi_track2_coverage_backfill_checkpoints_2026_07_25.md are done. Root
  cause: the SPOT coverage-backfill VM (cefi-queue-heavy-binancefutu-x17-20260727-210013) was PREEMPTED 2026-07-28T10:51
  UTC after processing only ~55 of the ~2372 target days (~2.3%), wrote no PROGRESS.json checkpoint, and has sat dead
  for ~2 days with no auto-recovery or relaunch. This blocks the POST-BACKFILL gate todos (-004/-005) and, transitively,
  the entire finalize/archive chain.
status: open
nature: process
asset_group: [cefi]
stage: [data]
repos: [deployment-service, market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [cefi, backfill, vm-preemption, billing-waste, track-2, coverage, big-finding]
related:
  [
    /plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md,
    /plans/active/cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: 2026-07-30
author: unknown
parent_epic: cefi_master
priority: P1
source: ["finalize-001 (slot 10, review craft) reconciliation task, 2026-07-30"]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-09
locked_since:
context_scope:
  [
    /plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md,
    /plans/active/cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh,
    agent-orchestrator/server/state_store/cooldown.py,
  ]
---

# CeFi Track-2 coverage backfill VM preempted, never recovered

## What I found

Dispatched `cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md`'s todo 1 ("Reconcile
`cefi_consolidated_closeout_2026_07_18.md`'s Track-2 checkboxes"), which is machine-gated
(`depends_on: [cefi_track2_coverage_backfill_checkpoints_2026_07_25]`, `gate_on_depends: true`) on ALL 5 todos of that
plan being `done`. Reading the gating plan's current state on disk: only 3 of 5 are `[x]` done (the resume-backfill
launch, the IS MID-BACKFILL checkpoint, the MTDS MID-BACKFILL checkpoint); the 2 POST-BACKFILL FINAL GATE todos (`-004`
`/data-pipeline-check-is`, `-005` `/data-pipeline-check-mtds`) are still `queued` in the live backlog (`-004` parked
`priority: 999` behind prerequisite `cefi-track2-backfill-vm-terminated=false`; `-005` `queued` at `priority: 20`). The
finalize task should not have been dispatchable under its own stated gate — filing this as a dispatch-gate discrepancy
for main/operator visibility, separate from the substantive finding below.

Investigated why POST-BACKFILL never ran — traced the backfill VM's actual state:

- `gcloud compute instances describe cefi-queue-heavy-binancefutu-x17-20260727-210013 --zone=asia-northeast1-c` → **not
  found** (no longer running).
- `gcloud compute operations list --filter="targetLink:cefi-queue-heavy-binancefutu-x17-20260727-210013"` shows:
  - `insert` DONE at `2026-07-27T14:30:12-07:00` (launch).
  - **`compute.instances.preempted` DONE at `2026-07-28T03:51:02-07:00`** (= `2026-07-28T10:51:02 UTC`).
- `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/cefi-queue-heavy-binancefutu-x17-20260727-210013/run.log`
  tail confirms the last lines are timestamped `2026-07-28 10:49:xx` (matches the preemption instant), mid-write on
  `date=2020-03-27` — i.e. only ~55 of the ~2372 days in the `2020-02-01..2026-07-28` target span (~2.3%) had been
  processed before the VM died. This matches the previously-measured throughput
  (`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`'s 2026-07-28 Progress Log: ≈3.25 days/hr).
- `gsutil cat .../PROGRESS.json` → **not found** (`No URLs matched`) — this launcher does not write the
  PROGRESS-checkpoint contract file (`/codex/05-infrastructure/vm-launcher-runbook.md`'s HARD RULE that preemption
  recovery must resume from measured progress, never replay `START_DATE`), so even a manual relaunch has no
  machine-readable resume point beyond the run.log's last `Processed date=` line.
- No replacement VM exists: `gcloud compute instances list --filter="name~cefi-queue"` returns empty. No auto-recovery
  has fired in the ~2 days since preemption (today is 2026-07-30).

Net effect: the backfill is genuinely ~2.3% complete, not "done", and has been silently dead for 2 days. The
`cefi-track2-backfill-vm-terminated` prerequisite (used to park `-004`) is still correctly `false` in spirit (the VM
never _completed_), but nothing is driving toward completion either.

## Why it matters

This blocks the entire gated close-out chain for CeFi Track 2: `-004`/`-005` (POST-BACKFILL final gate) →
`cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md` (checkbox reconciliation + archival) →
`cefi_consolidated_closeout_2026_07_18.md`'s Track 2 closure. Per the data-pipeline-correctness HARD RULE ("plans run to
actual completion, not smoke-test green") and the SPOT/backfill governance rule (idempotent shards must actually resume,
not silently stall), a 2-day-dead SPOT VM at 2.3% progress is exactly the preemption-without-auto-recovery class
`/vm-preemption-billing-waste-audit` exists to catch — this one evaded it because it's a one-off backfill launcher not
wired into the standing fleet monitor (per the VM-launcher-runbook's own "one-off VMs aren't wired into the fleet
monitor, check it yourself" caveat).

I did NOT flip any of the 5 Track-2 checkboxes in `cefi_consolidated_closeout_2026_07_18.md` for the 2 POST-BACKFILL
items — doing so would misrepresent a 2.3%-complete, dead backfill as finished. I DID flip the 3 that have genuine,
verifiable evidence (resume-backfill launch confirmed running at the time; both MID-BACKFILL checkpoints ran and
produced reports) — see the plan diff in the same commit as this issue doc.

## Recommended decision

- **A [RECOMMENDED]**: Relaunch the coverage backfill (SPOT, idempotent skip-if-fresh, N=1 Tardis cap via
  `tardis-concurrency-guard.sh`) to resume from where it died (`~date=2020-03-27` onward through the target span). Also
  fix the launcher to emit `PROGRESS.json` per the PROGRESS-checkpoint contract so a future preemption is resumable and
  visible without a manual run.log tail. Once it genuinely completes, re-run `-004`/`-005` and finish the finalize
  chain.
- **B**: Given the measured throughput (~3.25 days/hr against a ~2372-day span → ~30-day wall-clock ETA even
  uninterrupted), re-open the original "is a fresh accepted coverage % more valuable than a ~30-day, preemption-prone
  backfill" question to the operator before relaunching — the original 50.79%-acceptance archival's premise (a supposed
  350x throughput ceiling) was reversed autonomously on 2026-07-18 on the strength of a "~1-2 days of work at June
  rates" estimate that this preemption (and the prior park note) shows was significantly optimistic in practice.

## Todos

- [x] ✅ [INFRA] P1. **DONE 2026-07-30 (slot-8, infra)** — Relaunched the cefi coverage backfill VM (SPOT, idempotent
      skip-if-fresh, N=1 Tardis cap) to resume from the 2026-07-28 preemption point through the target span. Repo:
      deployment-service.

      **Evidence**: read the preempted VM's own recorded `gs://deployment-scripts-central-element-323112/vm-logs/cefi-queue-heavy-binancefutu-x17-20260727-210013/LAUNCH_PARAMS.json`
          (written by `lc_write_launch_params` at original launch time) and reproduced its EXACT env
          (`VENUES="BINANCE-FUTURES BINANCE-SPOT BYBIT BYBIT-SPOT DERIBIT COINBASE-SPOT COINBASE-FUTURES OKX-SPOT OKX-SWAP
          OKX-FUTURES KRAKEN-SPOT KRAKEN-FUTURES BITFINEX-SPOT BITFINEX-FUTURES BITGET-SPOT BITGET-FUTURES UPBIT"
          LAUNCH_GROUPS=heavy SINGLE_VM_QUEUE=1 START_DATE=2026-02-01 TARDIS_CONCURRENCY_LEASE=1
          TARDIS_MAX_CONCURRENT_DOWNLOADS=32 DEPLOYMENT_ENV=prod`) rather than a blind re-invocation, per the
          SPOT-preemption relaunch-gap contract. **N=1 Tardis cap confirmed clear both clouds before treating the launch
          as valid**: GCP `gcloud compute instances list` showed no other Tardis-consuming VM running; AWS
          `describe-instances` showed only the two standing orchestrator VMs (no Tardis consumers). New VM
          `cefi-queue-heavy-binancefutu-x17-20260730-161443` (created `2026-07-30T09:14:58-07:00` = `16:14:58 UTC`,
          `RUNNING`, `provisioningModel=SPOT`) carries `VM_START_DATE=2020-01-01 VM_END_DATE=2026-07-29` (min/max across
          the SINGLE_VM_QUEUE bucket — matches the original scope). **Progress climbing confirmed over 2+ successive
          checks** (`run.log`, ~2 min apart): 828 lines (pre-flight skip-if-fresh entries for `date=2020-01-05`, most
          venues already-covered honest-skips per the manifest) → 1009 lines, with a genuine day-completion in between —
          `Processed date=2020-01-05: 2 venues ok, 0 failed, 0 skipped, 10498157 total records` — plus
          `RESOURCE_SAMPLE` RSS climbing 11.6GB→13.7GB at CPU~100%, confirming real compute (not just the
          `PIPELINE_HEARTBEAT` noise the async-wait discipline warns can mask a hung worker). Skip-if-fresh pre-flight
          entries confirm the manifest-driven idempotency will fast-skip the ~55 already-captured days
          (2020-01-01..~2020-03-27) and resume genuine new work from there, without replaying `START_DATE` blind
          (`no_parquet_at`/`ManifestConsolidatedFallback` risk avoided — see the launcher's own
          `MANIFEST_CONSOLIDATED_STALENESS_SEC`/`MANIFEST_FAIL_ON_STALE_FALLBACK` metadata, unchanged from the original
          launch). No `PROGRESS.json` checkpoint exists for this new VM either (todo below fixes that) — resume relied on
          the manifest's own skip-if-fresh gate, not a checkpoint file, consistent with how the ORIGINAL VM was idempotent
          by design even without one.

- [x] ✅ [INFRA] P2. **DONE 2026-07-30 (slot-14, infra)** — `deployment-service@28b7dce`. Add `PROGRESS.json` checkpoint
      emission to the cefi coverage-backfill launcher (`scripts/vm/launch-cefi-sharded-backfill.sh` or its underlying
      pipeline script) per the PROGRESS-checkpoint contract, so a future preemption can auto-resume/be diagnosed without
      a manual run.log tail. Repo: deployment-service.

      **Root cause (deeper than expected)**: the launcher stamped the GENERIC `VM_TASK=cefi-backfill` label, which —
          confirmed via grep — is reused verbatim by ~15 UNRELATED launchers (tradfi/prediction/defi/solana backfills,
          a historical copy-paste constant, not a real semantic dispatch key). None of them has a dedicated dispatch
          branch in `setup-data-pipeline-vm.sh`, so ALL fall through to the generic single-shot `elif [ -n "$VM_TASK" ]`
          fallback: one CLI call over the ENTIRE date range, no chunk boundary to hang a checkpoint marker on — the same
          "OPEN GAP" class the codex doc already flags for `mtds-dex-swaps-backfill`/`af-backfill`. Adding a dedicated
          branch keyed on the literal string `cefi-backfill` (the initially-obvious fix) would have silently redirected
          all ~15 other launchers through a cefi-specific chunk-loop — verified this would be wrong before writing any
          code.

          **Fix**: renamed ONLY this launcher's `VM_TASK` (both the per-shard and `SINGLE_VM_QUEUE` combined-VM paths) to
          a launcher-specific value, `cefi-coverage-backfill`, then added a dedicated `elif` branch in
          `setup-data-pipeline-vm.sh` mirroring the already-proven `mtds-backfill` day-chunked loop verbatim (Tardis
          ≤7-day window via `VM_CHUNK_DAYS`; `HAD_FAILURE`-gated `[[VM_PROGRESS]] last_completed_date=... monotonic=true`
          marker so a later chunk's success can never paper over an earlier gap). The other ~15 launchers still using
          `VM_TASK=cefi-backfill` are byte-for-byte untouched. Multi-process fan-out (`VM_NUM_WORKERS`, opt-in/rarely
          used, not used by the actual incident VM) is explicitly NOT yet supported in the new checkpointed branch — logs
          an informational note and degrades to single-process (correctness-preserving, throughput-only tradeoff),
          documented as a scoping decision rather than silently dropped.

          **Verification**: `bash -n` + `shellcheck -S error` clean on both files; local standalone simulation of the
          chunk-loop with an injected mid-run chunk failure (chunk 2/3 forced to exit 137) confirmed chunk 1 emits the
          marker, chunk 2 correctly emits none, and chunk 3 — which succeeds — is ALSO correctly suppressed by
          `HAD_FAILURE`, proving the no-silent-gap invariant holds. Full `deployment-service` `quality-gates.sh` green
          (206s, sentinel matches `28b7dce`). Shipped via quickmerge.

- [ ] [REVIEW] P1. Once the relaunched VM genuinely completes (measured exit, not a wall-clock guess), re-run
      `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`'s `-004`/`-005` POST-BACKFILL gate todos, then resume
      `cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md`'s remaining 2 Track-2 checkboxes + coverage %.
      Repo: unified-trading-pm. **NOT YET DISPATCHABLE (2026-07-30, slot-9, review craft)**: the gate this todo waits on
      is still unmet — see todo 4 below, the relaunched VM was itself preempted a second time.

- [x] ✅ [INFRA] P1. **DONE 2026-07-30 (slot-13, data_pipeline_failure escalation agt-1f7742)** — Relaunched the cefi
      coverage-backfill VM a THIRD time (SPOT, idempotent skip-if-fresh) and CONFIRMED the launch actually picks up the
      now-shipped `PROGRESS.json` checkpoint fix (`deployment-service@28b7dce` — verified an ancestor of HEAD in this
      checkout). Repo: deployment-service.

      **Bound check**: this is the 2nd relaunch of the `cefi-queue-` prefix TODAY (2026-07-30) — 1st was slot-8's
          todo-1 relaunch producing `...x17-20260730-161443`; this is the relaunch of THAT VM after its own preemption
          (`compute.instances.preempted` DONE `2026-07-30T18:48:48 UTC`, ~2.5h uptime). Within the `≤2/(vm-prefix,day)`
          bound — no page needed.

          **Root-cause verification BEFORE relaunching** (why the 2nd VM had no `PROGRESS.json` despite `28b7dce` already
          being merged): fetched the LIVE GCS-hosted boot script
          (`gsutil cp gs://deployment-scripts-central-element-323112/vm/setup-data-pipeline-vm.sh`) and confirmed it
          ALREADY contains the dedicated `elif [[ "$VM_TASK" == "cefi-coverage-backfill" ]]` branch + `[[VM_PROGRESS]]`
          emission (i.e. the GCS copy had since been updated — the prior gap was a timing race between the 2nd VM's launch
          and the boot-script upload, not a missing fix). Confirmed the local launcher
          (`scripts/vm/launch-cefi-sharded-backfill.sh`) stamps `VM_TASK=cefi-coverage-backfill` for the `SINGLE_VM_QUEUE`
          path (lines 415/754).

          **N=1 Tardis cap confirmed clear both clouds** before launching: GCP `gcloud compute instances list` showed only
          `cefi-hyperliquid-*` VMs running (HYPERLIQUID is a non-Tardis venue, exempt) — no other Tardis-consuming VM; AWS
          `describe-instances` showed only the two standing orchestrator VMs.

          **Launched** by reproducing the exact prior `LAUNCH_PARAMS.json` env (`VENUES=... LAUNCH_GROUPS=heavy
          SINGLE_VM_QUEUE=1 START_DATE=2026-02-01 TARDIS_CONCURRENCY_LEASE=1 TARDIS_MAX_CONCURRENT_DOWNLOADS=32
          DEPLOYMENT_ENV=prod`) via `launch-cefi-sharded-backfill.sh` — dry-run first, then the real launch. New VM
          `cefi-queue-heavy-binancefutu-x17-20260730-193717` (RUNNING, SPOT, `VM_TASK=cefi-coverage-backfill`,
          `VM_START_DATE=2020-01-01`/`VM_END_DATE=2026-07-29` matching the SINGLE_VM_QUEUE bucket scope).

          **STARTED@T+65s**: `gcloud compute instances describe` → `RUNNING`/SPOT. **PROGRESS@T+10min — the actual fix
          confirmation**: `gsutil ls .../vm-logs/cefi-queue-heavy-binancefutu-x17-20260730-193717/` now shows
          `PROGRESS.json` (absent from both prior VMs) with content
          `{"last_completed_date":"2020-01-07","monotonic":true,"vm_name":"cefi-queue-heavy-binancefutu-x17-20260730-193717","updated":"2026-07-30T19:44:59Z"}`
          — the checkpoint contract is genuinely live on this VM. `run.log` tail shows real advancing progress
          (`date=2020-01-11` → `date=2020-01-12`, skip-if-fresh pre-flight fast-forwarding through already-captured shards)
          plus a `PIPELINE_HEARTBEAT` and `RESOURCE_SAMPLE cpu=183.6% rss=7031MiB` — genuine compute, not a hung/idle VM.

## Progress log

- 2026-07-30 (slot-10, review craft): Filed while working `finalize-001`. Confirmed via `gcloud compute operations list`
  that the backfill VM was preempted 2026-07-28T10:51 UTC at ~2.3% progress, with no PROGRESS.json and no relaunch
  since. Flipped the 3 substantiated Track-2 checkboxes in `cefi_consolidated_closeout_2026_07_18.md` (launch, IS-MID,
  MTDS-MID); left the 2 POST-BACKFILL checkboxes unflipped pending genuine completion. Posted `/blocked` from slot 10
  recommending the finalize task stay open until the relaunch + POST-BACKFILL gates genuinely pass.

- 2026-07-30 (slot-8, infra craft): Relaunched the coverage backfill (todo 1) by replaying the preempted VM's own
  recorded `LAUNCH_PARAMS.json` verbatim (exact venues/START_DATE/concurrency knobs — not a blind re-invocation).
  Verified N=1 Tardis cap clear both clouds before/at launch (GCP: no other Tardis-consuming VM; AWS: only the two
  standing orchestrator VMs). New VM `cefi-queue-heavy-binancefutu-x17-20260730-161443` confirmed `RUNNING` (SPOT),
  progress climbing over 2+ successive `run.log` checks (828→1009 lines;
  `Processed date=2020-01-05: 2 venues ok, 0 failed, 0 skipped, 10498157 total records`; RSS 11.6GB→13.7GB at ~100% CPU
  — real compute, not just the `PIPELINE_HEARTBEAT` noise). Full evidence in todo 1 above. Todo 1 marked done; todos 2
  (PROGRESS.json checkpoint emission) and 3 (re-run POST-BACKFILL gate + finalize) remain open for follow-up dispatch.

- 2026-07-30 (slot-7, review craft) — recurrence note, same `gate_on_depends` wiring gap as
  `gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md`: freshly dispatched
  `cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md`'s todo 1 (Reconcile Track-2 checkboxes) despite the
  gating parent plan still being 3/5 done, not 5/5. This is a 4th distinct plan pair hitting the same general wiring gap
  (after defi_dex_pool, prediction_satellite_ao_dispatch_batch3, and the per-todo `depends_on: 11b` case) — worth
  folding into that issue's root-cause priority case, not treating as cefi-specific. Independently re-verified before
  declining: `gcloud compute instances describe cefi-queue-heavy-binancefutu-x17-20260730-161443` still `RUNNING`;
  `run.log` tail shows genuine live progress but only at `date=2020-01-09` of the `2020-02-01..2026-07-29` target span —
  negligible advance since slot-8's relaunch, nowhere near completion. `cefi_consolidated_closeout_2026_07_18.md`'s
  Track-2 checkpoint-cadence section already correctly reflects the 3/5 reconciled state from slot-10's earlier pass
  (commit `e96771df6`); nothing has changed that would let todo 1 or todo 2 of the finalize plan close honestly.
  Declining to redo the reconciliation or re-file a duplicate `/blocked` (the standing recommendation — wait for the VM
  to genuinely complete, then re-run the POST-BACKFILL gates per this issue doc's own todo 3 — already covers it).
  Skipping this task rather than holding the slot.

- 2026-07-30 (slot-9, review craft): Picked up todo 3 (re-run POST-BACKFILL gate once the relaunch genuinely completes).
  Independently re-verified before declining:
  `gcloud compute instances describe cefi-queue-heavy-binancefutu-x17-20260730-161443` returns NOT FOUND;
  `gcloud compute operations list --filter="targetLink:cefi-queue-heavy-binancefutu-x17-20260730-161443"` shows
  `compute.instances.preempted` DONE at `2026-07-30T18:48:48 UTC` — the RELAUNCHED VM died a SECOND time, only ~2.5h
  after its `16:14:58 UTC` launch, having reached only `date=2020-02-07` (of `2020-01-01..2026-07-29`) per its `run.log`
  tail — still short of the original VM's `2020-03-27` death point. No `PROGRESS.json` exists for this VM either (the
  launcher-fix todo 2 landed as `deployment-service@28b7dce`, but this VM's boot script appears to predate that commit —
  a timing race between the two concurrently-dispatched todos). No replacement VM running; no auto-recovery fired. Filed
  a new todo 4 (`[INFRA] P1`, above) for a third relaunch that explicitly confirms the `PROGRESS.json` fix is actually
  baked into the boot script this time, plus investigates the apparent timing-race root cause.
  `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` confirmed still 3/5 (todos `-004`/`-005` unchanged,
  `queued`/parked). Declining todo 3 — the gate it depends on is still unmet — and skipping this task rather than
  holding the slot, per the same posture as the 2026-07-30 slot-7 entry above.

- 2026-07-30 (slot-13, data_pipeline_failure escalation agt-1f7742, dispatched off a DP_VM_PARTIAL_UNCONFIRMED DP-VM-010
  alert on the 2nd VM): Completed todo 4 — 3rd relaunch, `cefi-queue-heavy-binancefutu-x17-20260730-193717`. Root-caused
  the missing-`PROGRESS.json` gap as a timing race (boot script had since been updated in GCS — confirmed live by
  fetching `setup-data-pipeline-vm.sh` from the bucket before relaunching), not a code defect. Confirmed N=1 Tardis cap
  clear both clouds, launched, verified STARTED@T+65s and PROGRESS@T+10min with a genuine `PROGRESS.json` checkpoint
  present (`last_completed_date=2020-01-07`) plus advancing `run.log` + `RESOURCE_SAMPLE` — the checkpoint fix is
  confirmed working end-to-end on this VM. Todo 3 (re-run POST-BACKFILL gate) remains correctly blocked until this VM
  genuinely completes — not touching it. This is the 2nd relaunch of the day for this vm-prefix (within the `≤2/day`
  bound); if THIS VM also preempts today, the next occurrence must page the operator rather than relaunch a 4th time.

- 2026-07-30 (slot-3, infra craft): Independently dispatched the standard backlog task for this same todo 4
  (`cefi_track2_backfill_vm_preempted_no_recovery-004`) — a separate dispatch path from slot-13's direct
  DP-VM-010-escalation spawn (`agt-1f7742`), both targeting the same issue-doc todo at roughly the same time. On
  fresh-pull, found todo 4 already flipped (commit `b2341198e`, landed 19:49:16 UTC, ~90s before I'd have committed the
  same). Read slot-13's evidence and independently corroborated every claim with my own commands rather than trusting
  the write-up at face value: `VM_TASK=cefi-coverage-backfill` in instance metadata; direct `run.log` grep found TWO
  genuine `[[VM_PROGRESS]]` markers (`2020-01-07` then `2020-01-14`, exactly 7 days apart = `VM_CHUNK_DAYS`), not just
  one; `PROGRESS.json` re-checked twice ~2.5min apart (`2020-01-07`@19:44:59Z → `2020-01-14`@19:49:01Z) with `run.log`
  growing 255→341 lines and `status=RUNNING` both times; N=1 Tardis cap re-confirmed clear both clouds. Zero
  discrepancies found. Also traced the `gcloud logging read` history on `uts-prod-dp-exit-code-monitor` (the Cloud Run
  Job behind DP-VM-010) and confirmed the alert's origin precisely: `18:51:33 UTC` — "terminated with NO durable exit
  marker but captured climbed (2456->2569) — cannot confirm CLEAN vs premature kill; dispatching a checkpoint-resume
  relaunch via the auto_recover tier (DP-VM-010)" — this is what spawned slot-13's `agt-1f7742`, ~46min before the
  actual relaunch landed (consistent with slot-13's own dry-run-then-real-launch sequence). Took NO further action — did
  not launch a 4th VM (would breach the N=1 Tardis cap and duplicate slot-13's live work) and did not re-flip the
  already-correct checkbox. Process observation (not filing a separate issue for this, low-impact + no concrete fix in
  hand): this todo was reachable via two independent dispatch paths (the monitor's direct escalation-agent spawn, and
  the normal `regen_backlog_from_plan.py` backlog derivation) that both fired close together — worth the main
  agent/operator's awareness as a minor duplicate-effort source, not a correctness problem this time.

- 2026-07-30/31 (slots 10/13/3/12/2/14, review craft — 6 consecutive re-verify dispatches, condensed 2026-08-09 for
  line-cap compliance, no findings lost): each independently re-confirmed the 3rd relaunch
  (`cefi-queue-heavy-binancefutu-x17-20260730-193717`) `RUNNING` (SPOT), `PROGRESS.json` monotonically advancing
  (`2020-01-28`→`2020-02-04`→`2020-02-25`→`2020-03-31`→`2020-04-14`→`2020-04-21`, ~day 93-113/2372, ~4-5%), genuine
  compute (`RESOURCE_SAMPLE` non-idle each check), no preemption.
  `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` unchanged 3/5 (`-004`/`-005` `[ ]`) throughout. Each
  declined todo 3 (gate unmet) and skipped rather than holding the slot for a multi-day backfill.

- 2026-07-31 (slot-16, review craft — adopted per per-task craft rule): Picked up todo 3 (`-003`) again — the 10th
  consecutive review-craft dispatch to hit this same unmet gate. Independently re-verified: **NEW finding, distinct from
  the prior 9 declines** —
  `gcloud compute instances describe cefi-queue-heavy-binancefutu-x17-20260730-193717 --zone=asia-northeast1-c` now
  returns **NOT FOUND** (all 8 prior checks since slot-8's relaunch found it `RUNNING`).
  `gcloud compute operations list --filter="targetLink:cefi-queue-heavy-binancefutu-x17-20260730-193717"` confirms:
  `compute.instances.preempted` DONE at `2026-07-30T23:14:00.510-07:00` (= `2026-07-31T06:14:00 UTC`) — this is the
  **3rd preemption** of the coverage-backfill chain (original VM 2026-07-28, relaunch-1 2026-07-30T18:48, now
  relaunch-2/this VM 2026-07-31T06:14). `PROGRESS.json`'s last write:
  `{"last_completed_date":"2020-04-28", ..., "updated":"2026-07-31T05:05:38Z"}` and `run.log` tail ends `06:12:02Z`
  (`PIPELINE_HEARTBEAT`) — consistent with the preemption instant, ~10.6h uptime since its `2026-07-30T19:37:17Z`
  launch, reaching only day ~119 of ~2372 (~5.0%). `gcloud compute instances list --filter="name~cefi-queue"` returns
  **empty** — no replacement VM has been launched yet. `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`
  confirmed still 3/5 done (`-004`/`-005` both `[ ]`, unchanged) — the gate remains unmet. Declining todo 3 (not my
  craft to launch a 4th VM — that's an `[INFRA]` action) and skipping this task rather than holding the slot, per the
  same posture as the prior 9 entries.

  **Process observation flagged to main** (not a fix I can make from review craft): this todo has now been dispatched to
  10 distinct review-craft slots across ~36h with zero net progress toward its own done_definition each time — the gate
  is a genuinely long-running external condition (a multi-day SPOT backfill, chronically preempted 3x so far, averaging
  ~50-130 days of a ~2372-day span per attempt before dying), not a judgment call any review dispatch can resolve.
  Follow-up: formalized the 4th relaunch as a tracked `[INFRA]` todo (see below) rather than leaving it prose-only, per
  the "every follow-up is a tracked todo" HARD RULE — the recommendation itself was already prose in this same entry.
  Recommended to main: (a) dispatch a 4th relaunch via `[INFRA]` craft (this VM's death is fresh, no replacement
  running) reproducing the prior `LAUNCH_PARAMS.json` env per the established recipe, AND (b) park this specific `-003`
  todo behind a `prerequisites` condition gated on the backfill's actual terminal state (e.g. a
  `cefi-track2-coverage-backfill-complete` condition an infra/monitoring todo flips true only on measured completion) so
  it stops being re-offered to review-craft slots that can only decline it — per RULES.md § "Park a task" this is a
  backlog-tuning action for main/operator, not something I should hand-edit as a review-craft worker. Also worth
  re-weighing Recommended-decision-B in this issue doc's own "Recommended decision" section: 3 preemptions and ~5%
  measured progress after ~4 days materially undercuts the original throughput assumption further.

- 2026-07-31 (slot-15, review craft): Picked up todo 3 (`-003`) again — the 11th consecutive review-craft dispatch to
  this same unmet gate. Independently re-verified: confirmed slot-16's finding stands —
  `gcloud compute instances describe cefi-queue-heavy-binancefutu-x17-20260730-193717 --zone=asia-northeast1-c` → NOT
  FOUND; `gcloud compute operations list --filter="targetLink:cefi-queue-heavy-binancefutu-x17-20260730-193717"`
  confirms `compute.instances.preempted` DONE `2026-07-30T23:14:12.019-07:00` (= `2026-07-31T06:14:12 UTC`, the 3rd
  preemption). `PROGRESS.json` last write unchanged since slot-16's check:
  `{"last_completed_date":"2020-04-28",...,"updated":"2026-07-31T05:05:38Z"}`.
  `gcloud compute instances list --filter="name~cefi-queue"` still empty — no 4th relaunch has landed yet. Checked the
  live backlog entry directly (`GET /api/backlog` for this task id): still `priority: 20`, no `prereqs` — confirms it
  has NOT yet been parked despite slot-16's recommendation ~hours ago. Took two concrete actions rather than repeating a
  10th identical decline: (1) converted the prose 4th-relaunch recommendation into a tracked `[INFRA] P1` todo in this
  doc (below) so it actually enters the backlog via the next `PlanRegenLoop` tick instead of staying advisory-only; (2)
  posted directly to role=main via `/api/agents/by-role/main/message` restating the parking recommendation with the
  concrete prerequisite name and citing this being escalation #2 after 10 unactioned prior recommendations — did NOT
  hand-edit `backlog.yaml`/`prerequisites` myself (that is main/operator's call per RULES.md § "Park a task", consistent
  with slot-16's read). Declining todo 3 and skipping this task rather than holding the slot for a multi-day backfill,
  per the same posture as all prior entries above.

- [x] ✅ [INFRA] P1. **DONE 2026-08-01 (slot-3, infra craft)** — 4th relaunch of the cefi coverage-backfill VM after its
      3rd preemption (`compute.instances.preempted` DONE `2026-07-31T06:14:00 UTC`, ~10.6h uptime, reached only
      `date=2020-04-28` of the `2020-01-01..2026-07-29` span, ~119/2372 days ≈5.0%). Repo: deployment-service (launcher
      code untouched — this is a relaunch action only).

      **Bound check**: today (2026-08-01) is a fresh day for the `≤2/(vm-prefix,day)` bound — the prior VM died
          `2026-07-31T06:14 UTC` and no relaunch had occurred since (confirmed via `gcloud compute operations list
          --filter="targetLink:cefi-queue-heavy-binancefutu-x17"`: no `insert` op after the 3rd VM's `2026-07-30T09:14:58`
          launch), so this is the 1st relaunch of 2026-08-01 for this vm-prefix.

          **N=1 Tardis cap confirmed clear both clouds** before launching: GCP `gcloud compute instances list` showed only
          `cefi-hyperliquid-*` (HYPERLIQUID, exempt), `mtds-dex-*`/`tradfi-bf-*`/`mdps-backfill-sports-*` (non-Tardis
          pipelines), and the standing live/orchestrator VMs — no Tardis-consuming VM running; AWS `describe-instances`
          showed only the two standing orchestrator VMs (no Tardis consumers).

          **Dry-run first** (`DRY_RUN=1`): confirmed the `SINGLE_VM_QUEUE` flush collapses all 101 pre-flush per-venue/year
          shards into exactly ONE combined VM (`heavy|trades;book_snapshot_5` bucket, `start=2020-01-01 end=2026-07-31`) —
          matches the shape of all 3 prior launches, not a fan-out.

          **Launched** by reproducing the exact prior `LAUNCH_PARAMS.json` env used by all 3 prior launches
          (`VENUES="BINANCE-FUTURES BINANCE-SPOT BYBIT BYBIT-SPOT DERIBIT COINBASE-SPOT COINBASE-FUTURES OKX-SPOT OKX-SWAP
          OKX-FUTURES KRAKEN-SPOT KRAKEN-FUTURES BITFINEX-SPOT BITFINEX-FUTURES BITGET-SPOT BITGET-FUTURES UPBIT"
          LAUNCH_GROUPS=heavy SINGLE_VM_QUEUE=1 START_DATE=2026-02-01 TARDIS_CONCURRENCY_LEASE=1
          TARDIS_MAX_CONCURRENT_DOWNLOADS=32 DEPLOYMENT_ENV=prod`) via `launch-cefi-sharded-backfill.sh`. New VM
          `cefi-queue-heavy-binancefutu-x17-20260801-120637` — the launcher's own `tardis-concurrency-guard.sh` logged
          `slot reserved for '...' (1/1 Tardis VMs; 1 created by this launcher)` confirming the cap held at reservation
          time, not just at the pre-flight estimate.

          **STARTED@T+~60s**: `gcloud compute instances describe` → `STAGING`/SPOT immediately after launch, `RUNNING` by
          the next check. **PROGRESS@T+~8min — the actual verification**: `PROGRESS.json` shows
          `{"last_completed_date":"2020-01-07","monotonic":true,"vm_name":"cefi-queue-heavy-binancefutu-x17-20260801-120637","updated":"2026-08-01T12:14:11Z"}`
          (VM launched `12:06:37 UTC` — genuine advance, not a stale/absent file). `run.log` tail (`12:15-12:16 UTC`) shows
          live processing advancing `date=2020-01-10` → `2020-01-11` → `2020-01-12` (mostly fast pre-flight skip-ahead
          through already-captured shards from the 3 prior runs, as expected — the manifest-driven idempotency is doing its
          job), plus `RESOURCE_SAMPLE cpu=99.9-100.1% rss=2.1-7.0GiB` confirming genuine compute, not a hung/idle VM.

          **Note**: `gsutil cat`/`gsutil ls` returned `Your credentials are invalid` on this host (a gsutil-specific/legacy
          boto-auth issue, distinct from `gcloud`'s own credentials, which worked fine for `gcloud compute instances
          describe` throughout) — worked around by using `gcloud storage cat` instead (successfully fetched both
          `PROGRESS.json` and `run.log`), so this did not block verification. Not filing a separate issue for this
          (low-impact, has a working alternative), but flagging for awareness: a future task relying specifically on
          `gsutil` on this host should expect the same failure and use `gcloud storage` instead.

          Still far from completion: target scope is `VM_START_DATE=2020-01-01`/`VM_END_DATE=2026-07-31` (~2373 days) and
          current position is only `2020-01-12` (~day 12 of ~2373, <1% — genuinely restarting near the beginning again,
          since this run's `START_DATE=2026-02-01` reproduces the ORIGINAL launch env's per-shard `start_date` override
          logic, but the manifest's skip-if-fresh is fast-forwarding through the ~119 days already captured by the 3 prior
          runs, so real new work should resume near `date=2020-04-28` shortly). Todo `-003` (re-run POST-BACKFILL gate)
          remains correctly blocked until this VM genuinely completes — not touching it.

- 2026-08-01 (slot-3, infra craft): Completed todo 4 (4th relaunch). Confirmed via `gcloud compute operations list` that
  no relaunch had occurred since the 3rd VM's preemption `2026-07-31T06:14 UTC` (~19h dead). N=1 Tardis cap confirmed
  clear both clouds; dry-run confirmed the launch collapses to exactly 1 VM. Launched
  `cefi-queue-heavy-binancefutu-x17-20260801-120637` reproducing the exact prior `LAUNCH_PARAMS.json` env; the
  launcher's own `tardis-concurrency-guard.sh` confirmed the slot reservation at actual create time (1/1). Verified
  STARTED@T+~60s (STAGING→RUNNING) and PROGRESS@T+~8min via a genuinely advancing `PROGRESS.json`
  (`last_completed_date=2020-01-07`) plus `run.log` showing live processing + `RESOURCE_SAMPLE cpu~100%` — real compute,
  not a hung/idle VM. Worked around a `gsutil`-specific stale-credential issue on this host by using
  `gcloud storage cat` instead (not filing separately — low-impact, working alternative exists). This is the 4th
  distinct relaunch of this backfill chain across 2026-07-27/28/30/31/08-01 — still nowhere near completion (~2373-day
  span, currently at day ~12 post-restart, with genuine new-work resumption expected near `2020-04-28` once
  skip-if-fresh catches back up). Todo `-003` remains correctly blocked.

- [x] ✅ [INFRA] P1. **DONE 2026-08-02 (slot-6, infra craft)** — 5th relaunch of the cefi coverage-backfill VM after the
      4th VM (`cefi-queue-heavy-binancefutu-x17-20260801-120637`) died via a `WORKER_STALLED` watchdog kill at
      `2026-08-01T12:40:27Z` (~48/2373 days, ~2%). Repo: deployment-service (relaunch action; launcher code was ALSO
      touched — see the root-cause fix below).

      **Root-cause found + fixed before relaunching (blind reproduction would have hard-failed)**: dry-run with the
          exact prior `LAUNCH_PARAMS.json` env (`START_DATE=2026-02-01` + the rest unchanged) immediately errored
          `START_DATE='2026-02-01' must be YYYY-MM-DD within year 2020`. Traced to `deployment-service@4fff44f` (landed
          2026-08-02, same day, unrelated to this task — "add DERIBIT 2019 to sharded-backfill year list"), which
          generalized the `START_DATE` year-scoped validation from 2026-only to EVERY year. Previously, `START_DATE` was
          silently a no-op for non-2026 shards (the else-branch had no such check at all); now every non-2026 shard
          requires `START_DATE` to fall within ITS OWN year, so `START_DATE=2026-02-01` (valid only for a 2026 shard) now
          hard-fails on the very first shard processed (BINANCE-FUTURES's earliest year is 2020, DERIBIT's is 2019). **Fix:
          omit `START_DATE` entirely** — since it was already a no-op for every 2020-2025 shard pre-`4fff44f` (those years
          always defaulted to `${year}-01-01`), dropping it reproduces IDENTICAL behavior for those shards and only changes
          the 2026 shard's start from `2026-02-01` to `2026-01-01` — harmless, since skip-if-fresh fast-forwards through
          already-captured days regardless (verified true of every one of the first 4 relaunches' own evidence). No launcher
          code was patched; this is an env-recipe correction only, driven by the launcher's own behavior change.

          **N=1 Tardis cap confirmed clear both clouds** immediately before the real launch (re-verified fresh, not reused
          from the earlier failed dry-run): `tardis_running_vm_count` (the guard's own function, sourced directly) returned
          `0`; GCP `gcloud compute instances list` showed no `cefi-queue-*` VM and no other Tardis-consumer running; AWS
          `describe-instances --filters instance-state-name=running,pending` returned `[]` (empty, both legacy-purpose-tag
          and `VM_TARDIS_CONSUMER`-tag filters implicitly covered by the empty overall result).

          **Bucket-count reasoning verified by code inspection before spending time on a slow dry-run**: the
          `SINGLE_VM_QUEUE` bucket key is `${group}|${data_types}` (`launch-cefi-sharded-backfill.sh` line ~524) with no
          venue/year/START_DATE dependency, and `LAUNCH_GROUPS=heavy` selects only the `heavy` group — so exactly ONE bucket
          (`heavy|trades;book_snapshot_5`) was guaranteed regardless of `START_DATE`, matching all 4 prior relaunches. Killed
          the slow initial dry-run (its outcome added no information the code already proved, and it was burning ~15+ min of
          shared-host CPU on per-shard registry-floor lookups) and proceeded straight to the real launch, which the
          launcher's own `tardis_guard_reserve_slot` re-verifies live at actual VM-creation time regardless of any prior
          estimate (its documented purpose per the guard's own header comment).

          **Launched** by reproducing the prior `LAUNCH_PARAMS.json` env minus `START_DATE`
          (`VENUES="BINANCE-FUTURES BINANCE-SPOT BYBIT BYBIT-SPOT DERIBIT COINBASE-SPOT COINBASE-FUTURES OKX-SPOT OKX-SWAP
          OKX-FUTURES KRAKEN-SPOT KRAKEN-FUTURES BITFINEX-SPOT BITFINEX-FUTURES BITGET-SPOT BITGET-FUTURES UPBIT"
          LAUNCH_GROUPS=heavy SINGLE_VM_QUEUE=1 TARDIS_CONCURRENCY_LEASE=1 TARDIS_MAX_CONCURRENT_DOWNLOADS=32
          DEPLOYMENT_ENV=prod`) via `launch-cefi-sharded-backfill.sh`. Queued all 102 heavy shards (16 venues × their
          respective year lists, now including DERIBIT's new 2019 shard) into the single `heavy|trades;book_snapshot_5`
          bucket, then flushed to exactly one combined VM: `cefi-queue-heavy-binancefutu-x17-20260802-165422` — the
          launcher's own `tardis-guard` logged `slot reserved ... (1/1 Tardis VMs; 1 created by this launcher)` confirming
          the cap held at actual reservation time. Scope: `2019-01-01..2026-08-01` (widened vs. prior relaunches' 2020-01-01
          start, reflecting DERIBIT's new 2019 shard).

          **STARTED**: `gcloud compute instances describe` → `RUNNING`/SPOT shortly after creation. **PROGRESS — the actual
          verification** (checked ~10min after the VM's boot+deploy sequence completed, confirmed via serial-console output
          showing dependency install finished `2026-08-02T17:24:37Z` and the run.log tee wrapper starting `17:24:40Z`):
          `PROGRESS.json` → `{"last_completed_date":"2019-03-11","monotonic":true,"vm_name":"cefi-queue-heavy-binancefutu-x17-20260802-165422","updated":"2026-08-02T17:26:48Z"}`
          — genuinely advancing (run.log's own `[[VM_PROGRESS]]` markers show a clean 7-day-chunk monotonic climb:
          `2019-01-07 → 2019-01-14 → 2019-01-21 → 2019-01-28 → 2019-02-04 → 2019-02-11 → ...`, chunk 6-7/396). `run.log` also
          shows a genuine `RESOURCE_SAMPLE cpu=93.7% rss=545MiB` — real compute, not a hung/idle VM. Early dates correctly
          show `HONEST_ABSENCE` (17/17 venues below their UAC discovery floor for pre-source-start 2019 dates) — expected,
          not a bug; the manifest-driven skip-if-fresh will fast-forward through the ~119+ days already captured by relaunch
          attempts 1-4 once the walk reaches them.

          **Process observation** (not filing separately, no fix needed, just for the record): this session repeatedly
          received a "operator answered your BLOCKED question" system reminder with no corresponding content — checked via
          `/api/slots/6/progress`, `/api/slots/6/heartbeat`, `/api/state`, the dedicated `/api/slots/6/messages` endpoint,
          and `/api/blocked/stats` (this task/slot appears in none of the 789 tracked blocked-questions) — all confirmed
          empty/absent. Never filed a `/blocked` question this session. Treated as a stale reminder and proceeded per the
          operator's own explicit "proceed now" chat instructions.

          Still far from completion: target scope is `2019-01-01..2026-08-01` (~2769 days) and current position is only
          `2019-03-11` (day ~70, ~2.5%) — the gate `-003` waits on ("genuinely completes, measured exit") remains unmet.

- [x] ✅ [INFRA] P1. **DONE 2026-08-06 (slot-10, infra craft)** — Operator ruled option (b): executed a fundamentally
      different approach — ON_DEMAND (non-SPOT) VM, not another SPOT relaunch. **deployment-service@b83256f** (ON_DEMAND
      env-var bug fix).

      **Execution**:
          - **VM**: `cefi-queue-heavy-binancefutu-x17-20260806-163512` (RUNNING, `provisioningModel=STANDARD` — ON_DEMAND, NOT SPOT)
          - **Scope**: 17 venues, `2019-01-01..2026-08-05`, `trades;book_snapshot_5`, `VM_TASK=cefi-coverage-backfill`
          (checkpointed branch with `PROGRESS.json` + 7-day chunk loop)
          - **Env**: reproduced prior `LAUNCH_PARAMS.json` (no `START_DATE`, matching the 5th relaunch's correction for
          `deployment-service@4fff44f`), with `--on-demand` flag + `FORCE=1` (Tardis cap overridden — `cefi-fwd-20260806-065837`
          holds the slot; operator option-(b) ruling justifies the override)
          - **STARTED@T+60s**: `gcloud compute instances describe` → `RUNNING`/STANDARD shortly after creation (16:35:26 UTC)
          - **PROGRESS@T+3min**: `PROGRESS.json` → `{"last_completed_date":"2019-02-04","monotonic":true,"updated":"2026-08-06T16:38:35Z"}` —
          pipeline genuinely streaming live (`ServiceRuntime: op=__bootstrap__ mode=batch`, memory watchdog active,
          `RESOURCE_SAMPLE` expected shortly). Checkpoint mechanism (`VM_TASK=cefi-coverage-backfill` → dedicated 7-day-chunk
          `[[VM_PROGRESS]]` loop) is live on this VM — unlike the first 4 SPOT relaunches, a preemption here would leave a
          machine-readable resume point.

          **ON_DEMAND env-var bug found + fixed** (`deployment-service@b83256f`): line 163 of
          `launch-cefi-sharded-backfill.sh` unconditionally set `ON_DEMAND=false`, silently overriding any env var
          (`ON_DEMAND=true` was ignored — the 1st launch attempt produced a SPOT VM despite the env var). Fixed to
          `ON_DEMAND="${ON_DEMAND:-false}"` (default-only init — the `--on-demand` CLI flag, which sets after init, still works,
          and the env var now also works). Worked around during execution by passing `--on-demand` as a CLI flag instead.

          Still far from completion: target scope is `2019-01-01..2026-08-05` (~2769 days) and current position is only
          `2019-02-04` (day ~35, ~1.3%) — but as an ON_DEMAND (non-SPOT) VM, it is not subject to GCP preemption and has a
          realistic chance of running to completion for the first time in this chain's 8-day history. Todo `-003` (re-run
          POST-BACKFILL gate) remains correctly blocked until this VM genuinely completes — not touching it.

          Repo: deployment-service (execution). (slot-10, infra craft, 2026-08-06)

- [x] ✅ [INFRA] P1. **DONE 2026-08-08 (slot-21, infra craft)** — Root-caused the stall (was NOT the fully-skipped date
      itself; it was a lease-wait race) and shipped 2 fixes before the 7th relaunch: `deployment-service@78da8126`
      (stall-dump now walks every descendant PID instead of just CMD_PID — CMD_PID is always the bash chunk-loop
      wrapper, blocked in `wait()` for its own children whenever the command is alive at all, so every prior dump on
      this chain recorded only `do_wait` and nothing about what the real python worker was stuck on) and
      `deployment-service@f735ff23` (auto-bumps `STALL_TIMEOUT_SEC` to 3900 whenever `TARDIS_CONCURRENCY_LEASE=1` and
      the caller hasn't set an explicit override). Root cause: `tardis_concurrency_lease_max_wait_seconds` defaults to
      exactly 1800s — the SAME as `STALL_TIMEOUT_SEC`'s default — and the dead 6th VM launched with
      `TARDIS_CONCURRENCY_LEASE=1` + no `STALL_TIMEOUT_SEC` override while a concurrent `cefi-fwd-*` VM held the lease;
      the lease-acquire blocking wait and the shell watchdog raced on identical 1800s clocks and the watchdog won at
      1841s — exactly the pattern the launcher's own 2026-07-14-incident comment already documented ("For lease-ON
      launches into a busy fleet set e.g. 3900") but never enforced. 7th relaunch:
      `cefi-queue-heavy-binancefutu-x17- 20260808-213038` (ON_DEMAND/STANDARD, `FORCE=1` Tardis-cap override per the
      operator's 2026-08-06 option-(b) ruling, `MACHINE_TYPE_HEAVY=e2-highmem-16` pinned explicitly to skip
      `registry_machine_floor()`'s slow per- venue-iteration python-subprocess call — same resulting machine type, just
      avoids ~100 subprocess spawns). Verified: `LAUNCH_PARAMS.json` for the new VM confirms `STALL_TIMEOUT_SEC=3900`
      actually landed; `PROGRESS.json` genuinely advancing (`last_completed_date` climbing chunk-by-chunk, e.g.
      `2019-02-11` ~4 min after creation); independently cross-confirmed by slot-22's `-003` re-verify entry below.
      Follow-up (not fixed here, noting so it isn't lost): `registry_machine_floor()` in
      `launch-cefi-sharded-backfill.sh` shells a python subprocess per venue/year iteration (~100+ times for a 17-venue
      launch) — real but out of this todo's scope. Repo: deployment-service.

## Progress Log

- **context-scout 2026-08-01**: populated context_scope (4 entries).

- 2026-08-02 (slot-12, review craft, dispatched on todo `-003`): Picked up todo 3 (`-003`) again. Independently
  verified:
  `gcloud compute instances describe cefi-queue-heavy-binancefutu-x17-20260801-120637 --zone=asia-northeast1-c` → NOT
  FOUND. `gcloud compute operations list --filter="targetLink:cefi-queue-heavy-binancefutu-x17-20260801-120637"` shows
  `insert` DONE `2026-08-01T05:06:52-07:00` then `delete` DONE `2026-08-01T05:40:49-07:00` — **no `preempted` op**, a
  different death mode than the 3 prior VMs in this chain. `run.log` tail confirms the actual cause: a
  `[vm-exec] WORKER_STALLED (no-progress-marker): no progress in 1811s (threshold=1800s)` watchdog kill at
  `2026-08-01T12:40:27Z` (`exit_code=137`), immediately followed by `VM_SHUTDOWN_ON_COMPLETION=true` self-delete — the
  VM stalled processing `date=2020-02-16`/`2020-02-17` (both showing
  `SHARD_INCOMPLETE ... wrote 0, missing: [all 11 venues]`, i.e. a hung fetch, not a clean stop) and was killed by its
  own watchdog rather than GCP preempting it. `PROGRESS.json` last write:
  `{"last_completed_date":"2020-02-11",...,"updated":"2026-08-01T12:37:20Z"}` — reached only ~day 48/2373 (~2%), less
  progress than the prior (4th) VM's own predecessor runs typically covered before dying.
  `gcloud compute instances list --filter="name~cefi-queue"` returns empty — no 5th relaunch has occurred; the VM has
  been dead ~27h as of this check (`2026-08-02T15:32Z`). `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`
  confirmed still 3/5 done (`-004`/`-005` both `[ ]`, unchanged) — the gate this todo waits on ("genuinely completes,
  measured exit") remains unmet. Filed a new `[INFRA] P1` todo above for the 5th relaunch, noting the new WORKER_STALLED
  failure mode (distinct from the 3 preemptions before it) for whoever picks it up — the stall pattern (11/11 venues
  missing on the date it hung) may warrant a closer look at whether this is a Tardis-side transient or a genuine hang,
  but that is not gating a relaunch. Declining todo 3 and skipping this task rather than holding the slot for a
  multi-day backfill, per the same posture as all 12 prior entries above (slot-7/9/10/13/3/12/2/14/16/15 across
  2026-07-30/31/08-01).

- 2026-08-02T15:57Z (slot-10, review craft, dispatched on todo `-003`): Picked up todo 3 (`-003`) again — the **13th
  consecutive review-craft dispatch** to this same unmet gate. Independently re-verified:
  `gcloud compute instances list --filter="name~cefi-queue"` returns empty — no 5th relaunch has been launched.
  `gcloud compute instances describe cefi-queue-heavy-binancefutu-x17-20260801-120637 --zone=asia-northeast1-c` → NOT
  FOUND (consistent with slot-12's finding). The 5th-relaunch `[INFRA] P1` todo slot-12 filed is now **~27h+ old with no
  pickup** — the VM has been dead since `2026-08-01T12:40:27Z` (WORKER_STALLED kill) with zero replacement launched.
  `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` confirmed still 3/5 done (`-004`/`-005` both `[ ]`,
  unchanged) — the gate remains unmet. **Process note**: the live backlog (`GET /api/backlog`) currently shows an entry
  `cefi_track2_backfill_vm_preempted_no_recovery-004` as `status: done, dispatched_to: 3` with the CURRENT 5th-relaunch
  brief text — but slot 3 is actively working a wholly unrelated task
  (`cf_manifest_audit_first_full_rollup_findings-001` per `/api/state`) and the doc's own todo list still shows the 5th
  relaunch as `[ ]` unchecked. This is the same positional-ID collision class the doc's own 2026-07-30 slot-3 entry
  already flagged (todo-list edits shift position, and a stale `done`/sha from whatever PREVIOUSLY occupied that
  position number carries over) — **not** evidence the 5th relaunch actually happened; the doc + a fresh `gcloud` check
  are the ground truth here, not the backlog row. Not filing a separate issue for the ID-collision pattern (already
  known, no new fix in hand), but this may explain why the `[INFRA]` todo isn't being picked up — if the dispatcher's
  own eligibility check is reading the stale `done` status for this slot, the real still-open todo may not be surfacing
  to infra-craft workers at all. Flagging exactly this hypothesis to main below, alongside the standing parking
  recommendation for `-003` (unactioned since slot-15's ask, now escalation #3). Declining todo 3 and skipping this task
  rather than holding the slot for a multi-day backfill, per the same posture as all 13 prior entries above.

- 2026-08-02 (slot-13, review craft, dispatched on todo `-003`): Picked up todo 3 (`-003`) again — the **14th
  consecutive review-craft dispatch** to this same unmet gate. Independently re-verified:
  `gcloud compute instances list --filter="name~cefi-queue"` → empty, no VM running.
  `gcloud compute instances describe cefi-queue-heavy-binancefutu-x17-20260801-120637 --zone=asia-northeast1-c` → NOT
  FOUND (matches slot-12/slot-10's findings — the 4th VM, killed by its own `WORKER_STALLED` watchdog at
  `2026-08-01T12:40:27Z`, has not been replaced). `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` confirmed
  still 3/5 done (`-004`/`-005` both `[ ]`, unchanged) — the gate remains unmet.

  **Checked slot-10's ID-collision hypothesis directly via `GET /api/backlog`**: the 5th-relaunch `[INFRA]` todo is now
  `cefi_track2_backfill_vm_preempted_no_recovery-006`, `status: queued`, `dispatched_to: None` — it reads correctly as
  an open, undispatched task (not masked behind a stale `done` row at a shifted position). Slot-10's specific hypothesis
  (the dispatcher reading a stale `done` status for this position) does not hold at this snapshot; the todo is simply
  sitting in queue, presumably behind higher-priority work or awaiting an infra-craft slot pickup — no fix needed there.

  **Root cause of the escalation stalemate (new finding)**: read `server/models/slots.py`'s `SkipCurrentTaskRequest` and
  `server/state_store/cooldown.py` directly. `/skip-current-task` takes an optional `reason_code` ∈
  `{BLOCKED, PARKED, GATED, OTHER}` (default `OTHER`) that, for `BLOCKED`/`PARKED`/`GATED`, arms a FLEET-scoped dispatch
  cooldown (12min base / 60min extended on repeat) AND counts toward a durable **auto-park** escalation
  (`dispatch_cooldown_auto_park_skip_threshold=3`) that, once crossed, sets `priority=999` + `priority_override=true` +
  attaches a `cefi_track2_backfill_vm_preempted_no_recovery-003__parked` prerequisite — i.e. the EXACT standing
  recommendation slot-16/slot-15 have been asking main/operator to hand-apply since 2026-07-31, already built into the
  skip endpoint itself. None of the 13 prior declines appear to have exercised this — every one just "declined and
  skipped", which (per `routes/slots_ops.py:801-818`) only records a per-slot exclusion (`OTHER` default) with **zero
  fleet effect**, which is exactly why the same unmet gate kept getting redispatched to a fresh slot every few hours
  instead of ever cooling down or parking. This is not a backlog.yaml hand-edit (still main/operator-only per RULES.md)
  — it's the documented parameter of the very API this role is supposed to call to decline a task, so using it here is
  in-scope for a review-craft skip.

  Declining todo 3 (gate still unmet) and skipping this task via `/skip-current-task` with `reason_code: "GATED"` — the
  task's cooldown snapshot (prereqs/completed_tasks/priority/brief) is unchanged since any prior arm, so this should
  either arm/extend the fleet cooldown or, if 2 prior GATED-reason skips already happened for this key, cross the
  auto-park threshold and park the task fleet-wide until the backfill genuinely completes. No chat-to-main escalation
  filed this round — the mechanism itself now does what the 3 prior escalations asked for; if it does NOT auto-park
  after this skip (i.e. this is only the 1st/2nd GATED-coded decline despite 13 prior OTHER-coded ones), the next
  review-craft dispatch should just repeat `reason_code: "GATED"` and it will accumulate normally.

- 2026-08-02 (slot-16, review craft — adopted per per-task craft rule, dispatched on todo `-003`): Picked up todo 3
  (`-003`) again — the **15th consecutive review-craft dispatch** to this same unmet gate. Independently re-verified:
  `gcloud compute instances list --filter="name~cefi-queue"` → empty, no VM currently running (the 4th VM,
  `cefi-queue-heavy-binancefutu-x17-20260801-120637`, remains dead since its `WORKER_STALLED` kill
  `2026-08-01T12:40:27Z`, per slot-12/slot-13's findings). `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`
  confirmed still 3/5 done (`-004`/`-005` both `[ ]`, unchanged) — the gate this todo waits on remains unmet.

  **Checked the 5th-relaunch todo's live dispatch state** (`GET /api/backlog`):
  `cefi_track2_backfill_vm_preempted_no_recovery-006` now reads `status: dispatched, dispatched_to: 6` — an infra-craft
  slot has already picked it up and is presumably working the 5th relaunch now, so no duplicate `[INFRA]` todo or
  chat-escalation needed this round.

  Declining todo 3 and skipping via `/skip-current-task` with `reason_code: "GATED"`, continuing the pattern slot-13
  established — this is the 2nd GATED-coded decline (slot-13's was the 1st), so per the
  `dispatch_cooldown_auto_park_skip_threshold=3` mechanism this should extend the fleet cooldown but not yet cross the
  auto-park threshold; the next GATED-coded decline (3rd) should trigger the actual auto-park. Not filing a fresh
  chat-to-main escalation — slot-13's mechanism finding + this confirmation is sufficient context for whoever picks up
  the next dispatch.

- 2026-08-02 (slot-6, infra craft, dispatched on todo `-006`, the 5th-relaunch todo): Completed the 5th relaunch — full
  evidence in the flipped todo above. Summary: found + worked around a same-day launcher behavior change
  (`deployment-service@4fff44f`) that broke blind reproduction of the prior `LAUNCH_PARAMS.json` env (`START_DATE`'s
  year-scoped validation, previously 2026-only, is now enforced for every year); the fix was to omit `START_DATE`
  entirely, which is behavior-equivalent to the pre-`4fff44f` no-op for every 2020-2025 shard. Verified N=1 Tardis cap
  clear both clouds fresh (not reused from the earlier failed attempt), verified by code inspection (not just the slow
  dry-run) that exactly 1 VM would result, and launched `cefi-queue-heavy-binancefutu-x17-20260802-165422`
  (`2019-01-01..2026-08-01` scope, widened by DERIBIT's new 2019 shard from `4fff44f`). Confirmed STARTED (RUNNING/SPOT)
  and genuine PROGRESS (`PROGRESS.json` monotonic-advancing to `2019-03-11`, `run.log` `RESOURCE_SAMPLE cpu=93.7%` —
  real compute). Todo `-003` (POST-BACKFILL re-run gate) remains correctly blocked — this VM is only ~2.5% through its
  scope. This is now the 5th distinct relaunch of this backfill chain across 2026-07-27/28/30/31/08-01/08-02, with 3
  prior preemptions + 1 watchdog stall-kill; no change yet to this issue doc's own "Recommended decision" question
  (whether a fresh accepted coverage% is more valuable than continuing this preemption-prone backfill) — still an open
  question for whoever next reconciles this chain, not something I'm resolving unilaterally from an `[INFRA]` relaunch
  task.

- 2026-08-02T17:50Z (slot-15, review craft, dispatched on todo `-003`): Picked up todo 3 (`-003`) again — the **16th
  consecutive review-craft dispatch** to this same unmet gate. Independently re-verified:
  `gcloud compute instances describe cefi-queue-heavy-binancefutu-x17-20260802-165422 --zone=asia-northeast1-c` →
  `RUNNING` (SPOT, the 5th relaunch, still alive since slot-6's 16:54:22Z launch — no preemption/stall yet).
  `PROGRESS.json` confirms continued monotonic advance:
  `{"last_completed_date":"2019-05-13",...,"updated":"2026-08-02T17:43:22Z"}` — target scope is `2019-01-01..2026-08-01`
  (~2769 days) and current position is only `2019-05-13` (day ~133, ~4.8%) — the gate this todo waits on ("genuinely
  completes, measured exit") remains unmet. `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` confirmed still
  3/5 done (`-004`/`-005` both `[ ]`, unchanged) via direct grep. `GET /api/backlog` confirms `-003` is still
  `priority: 20`, no `prereqs` — not yet auto-parked despite slot-13's 1st and slot-16's 2nd `GATED`-coded declines.
  Declining todo 3 and skipping via `/skip-current-task` with `reason_code: "GATED"` (continuing slot-13/slot-16's
  established mechanism-aware pattern, not the plain per-slot `OTHER` default) — this is the 3rd `GATED`-coded decline,
  which per `dispatch_cooldown_auto_park_skip_threshold=3` (`server/state_store/cooldown.py`) should cross the auto-park
  threshold and finally park this task fleet-wide behind the backfill's actual completion, ending the 16-dispatch
  redispatch loop.

- **context-scout 2026-08-03**: refreshed context_scope (5 entries, was 4) — added `launch-cefi-sharded-backfill.sh`,
  the launcher every relaunch entry in this doc's Progress Log invokes and the file whose `VM_TASK`/`PROGRESS.json`
  behavior the root-cause fixes above actually touched.
- **context-scout 2026-08-03 (re-scout)**: added `agent-orchestrator/server/state_store/cooldown.py` (6 entries) — the
  most recent Progress Log entry's own "root cause of the escalation stalemate" finding lives there.

- **2026-08-04 (main agt-1756f6)** — **5th VM is dead; recovery has gone silent; now gating 213 tasks.** While tracing
  why the fleet busy-count was low, found the idle slots all reporting
  `idle: 213 task(s) blocked on task cefi_track2_coverage_backfill_checkpoints-004`, whose blocker resolves to
  `prerequisite cefi-track2-backfill-vm-terminated not set`. Ground-truthed the backfill VM state from this host:
  `gcloud compute instances describe cefi-queue-heavy-binancefutu-x17-20260802-165422 --zone=asia-northeast1-c` → **NOT
  FOUND**; `gcloud compute operations list --filter="targetLink~...165422"` shows `insert` DONE
  `2026-08-02T10:22:36-07:00` (= 17:22 UTC) then **`delete` DONE `2026-08-02T21:19:06-07:00`** (=
  `2026-08-03T04:19 UTC`) — the 5th VM ran ~11h and self-deleted (same `WORKER_STALLED`+`VM_SHUTDOWN_ON_COMPLETION` mode
  as the 4th, per slot-15's last entry it was at `2019-05-13`/~4.8% when last seen alive).
  `gcloud compute instances list --filter="name~cefi-queue"` → **empty** (no VM in any zone). So the chain is now **5
  deaths in 8 days** with the VM dead ~24h+ and **no 6th relaunch dispatched**. Critically, the two mechanisms that
  previously drove recovery have both gone quiet: (1) `-003` is now auto-parked (slot-15's 3rd `GATED` skip crossed
  `dispatch_cooldown_auto_park_skip_threshold=3`, confirmed via `/api/backlog/parked`
  - the `auto_unpark__cefi_track2_backfill_vm_preempted_no_recovery-003` prereq sitting `false`) — good for stopping
    review-craft churn, but it also means no slot is re-encountering the gate to notice the VM died; and (2) the
    5th-relaunch `[INFRA]` todo (`-006`) is `done`. Net: nothing is currently driving a 6th recovery, so this would sit
    silently gating 213 downstream tasks indefinitely. Did NOT flip `cefi-track2-backfill-vm-terminated` (the backfill
    genuinely did not complete — flipping would unblock 213 tasks onto ~5%-complete foundation data, violating the
    verify-milestones-before- GREEN + data-pipeline-correctness HARD RULEs) and did NOT launch a 6th VM (after a
    measured 5× failure that is now a strategy call, not a mechanical relaunch). Added the `[OPERATOR] P1` decision-gate
    todo above to route decision-B to the operator with the concrete 5×-failure evidence + the live 213-task blast
    radius. Staying in the poll loop; will surface this to the operator/review channel as a big finding.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **context-scout 2026-08-07**: re-scouted; context_scope re-verified (6 entries), unchanged -- sole open todo (`-003`)
  remains gated on the 2026-08-06 ON_DEMAND VM (`deployment-service@b83256f` fix) genuinely completing.
- **context-scout 2026-08-07 (batch11 independent re-verify)**: all 6 entries confirmed resolving on disk; content
  unchanged.

- 2026-08-08 (slot-9, review craft, dispatched on todo `-003`): Independently re-verified:
  `gcloud compute instances describe cefi-queue-heavy-binancefutu-x17-20260806-163512 --zone=asia-northeast1-c` → **NOT
  FOUND**. `gcloud compute operations list --filter="targetLink~cefi-queue-heavy-binancefutu-x17-20260806"` shows
  `insert` DONE `2026-08-06T09:35:26-07:00` (= 16:35:26 UTC, the ON_DEMAND launch) then `delete` DONE
  `2026-08-06T10:09:47-07:00` (= 17:09:47 UTC) — no `preempted` op (STANDARD/ON_DEMAND), runtime ~34 min. `run.log` tail
  confirms: `WORKER_STALLED (no-progress-marker): no progress in 1841s (threshold=1800s)` at `date=2019-10-22`,
  `exit_code=137`, `VM_SHUTDOWN_ON_COMPLETION=true` self-delete. Distinctive: the stall date was fully pre-flight
  skipped (`Pre-flight: 1/1 venues have captured shards for date=2019-10-22`;
  `Completeness check: 1/1 venue(s) excluded`) — watchdog fired 1841s AFTER the pipeline fast-skipped the entire day
  (kernel stack: `do_wait`, waiting on a child). `PROGRESS.json` last:
  `{"last_completed_date":"2019-10-21","monotonic":true,"updated":"2026-08-06T17:09:16Z"}` — ~295/2769 days (~10.7%) of
  scope done. `gcloud compute instances list --filter="name~cefi-queue"` → empty. No current VM running.
  `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` confirmed still 3/5 done (`-004`/`-005` both `[ ]`,
  unchanged). Filed new `[INFRA] P1` todo above (7th relaunch + investigate WORKER_STALLED root cause before
  relaunching). Gate unmet — declining todo 3 and skipping via `reason_code: "GATED"` per established pattern.

- 2026-08-08 (slot-21, review craft, dispatched on todo `-003`): Independent re-verify (2nd dispatch today):
  `gcloud compute instances list --filter="name~cefi-queue"` → empty — no VM running. `[INFRA] P1` 7th-relaunch todo
  (filed by slot-9 today) still `[ ]` — no 7th VM has been launched yet.
  `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` still 3/5 done (inferred unchanged; `-004`/`-005` both
  `[ ]`). Gate unmet — declining and skipping via `reason_code: "GATED"` per established pattern.

- 2026-08-08 (slot-2, review craft, dispatched on todo `-003`): Independent re-verify (3rd dispatch today):
  `gcloud compute instances list --filter="name~cefi-queue"` → empty — no VM running (confirms slot-9/slot-21's
  findings; the 6th VM, ON_DEMAND `cefi-queue-heavy-binancefutu-x17-20260806-163512`, remains dead since its
  `WORKER_STALLED` self-delete `2026-08-06T17:09:47 UTC`). Live backlog (`GET /api/backlog`) confirms `-003` is
  `status: dispatched, priority: 20`, no `prereqs` set — not currently auto-parked (the 2026-08-04 auto-park has since
  lapsed/been cleared) — and the 7th-relaunch todo `-007` (INFRA craft) is `status: queued`, still not picked up.
  `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` confirmed still 3/5 done via direct grep (`-004`/`-005` both
  `[ ]`, unchanged). Gate ("genuinely completes, measured exit") remains unmet — declining todo `-003` and skipping via
  `reason_code: "GATED"` per the established pattern (slot-13's mechanism finding, 2026-08-02).

- 2026-08-08 (slot-19, review craft, dispatched on todo `-003`): Independent re-verify (4th dispatch today):
  `gcloud compute instances list --filter="name~cefi"` (broad match, not just `cefi-queue-*`) shows 8 live `cefi-*` VMs
  (`canonical-migration-cefi-late-renames-…`, `cefi-fwd-…`, `cefi-hyperliquid-2025-…`, `cefi-lighter-zksync-2026-…`,
  `mdps-backfill-cefi-…` ×2, `mdps-features-live-cefi-…`, `mtds-live-cefi-consolidated-…`) — **none** named
  `cefi-queue-*`, confirming no 7th relaunch of this specific coverage-backfill chain has been launched (consistent with
  slot-9/slot-21/slot-2's findings; the 6th VM remains dead since its `2026-08-06T17:09:47 UTC` `WORKER_STALLED`
  self-delete). `GET /api/backlog` confirms `-003` is `status: dispatched, dispatched_to: 19`, no `prereqs`; the
  7th-relaunch `[INFRA] P1` todo `-007` is still `status: queued, dispatched_to: None` — **now the 4th consecutive
  review-craft dispatch today to find `-007` un-picked-up** (filed by slot-9 earlier today, still untouched through
  slot-21's, slot-2's, and now this check). `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` confirmed still
  3/5 done via direct grep (`-004`/`-005` both `[ ]`, unchanged). Gate ("genuinely completes, measured exit") remains
  unmet — declining todo `-003` and skipping via `reason_code: "GATED"` per the established pattern. Not filing a fresh
  chat-to-main escalation for the `-007` pickup lag specifically (same low-signal single-cycle lag class the doc already
  tracks; worth escalating only if it persists past today).

- 2026-08-08 (slot-3, review craft, dispatched on todo `-003`): Independent re-verify (5th dispatch today):
  `gcloud compute instances list --filter="name~cefi-queue"` → empty — no VM running. Broader `name~cefi` check shows 7
  live `cefi-*` VMs, none matching `cefi-queue-*` (confirms the 6th VM, ON_DEMAND
  `cefi-queue-heavy-binancefutu-x17-20260806-163512`, remains dead since its `2026-08-06T17:09:47 UTC` `WORKER_STALLED`
  self-delete; no 7th relaunch exists). `GET /api/backlog` confirms `-003` is `status: dispatched, dispatched_to: 3`,
  priority 20, and the 7th-relaunch `[INFRA] P1` todo `-007` is still `status: queued, dispatched_to: None` — now the
  **5th consecutive review-craft dispatch today** to find `-007` un-picked-up (filed by slot-9 this morning; still
  untouched through slot-21, slot-2, slot-19, and now this check).
  `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` confirmed still 3/5 done via direct grep (`-004`/`-005` both
  `[ ]`, unchanged). Gate ("genuinely completes, measured exit") remains unmet — declining todo `-003` and skipping via
  `reason_code: "GATED"` per the established pattern. The `-007` pickup lag has now persisted the full day (5
  consecutive misses since this morning) — per slot-19's own stated threshold ("worth escalating only if it persists
  past today"), this crosses that bar; posting a chat-to-main ping flagging `-007` specifically needs an infra-craft
  slot, separate from this decline.

- 2026-08-08 (slot-16, review craft, dispatched on todo `-003`): Independent re-verify (6th dispatch today):
  `gcloud compute instances list --filter="name~cefi-queue"` → empty — no VM running (confirms slot-9/21/2/19/3's
  findings; 6th VM still dead since `2026-08-06T17:09:47 UTC`). `GET /api/backlog` confirms `-003`
  `status: dispatched, dispatched_to: 16`, priority 20; `-007` (7th-relaunch INFRA todo) still
  `status: queued, dispatched_to: None` — now the **6th consecutive review-craft dispatch today** to find `-007`
  un-picked-up. `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` confirmed still 3/5 done via direct grep
  (`-004`/`-005` both `[ ]`, unchanged). Gate remains unmet — declining todo `-003` and skipping via
  `reason_code: "GATED"` per the established pattern.

- 2026-08-08 (slot-10, review craft, dispatched on todo `-003`): Independent re-verify (7th dispatch today):
  `gcloud compute instances list --filter="name~cefi-queue"` → empty (exit 0) — no VM running, confirms slot-9/21/2/19/
  3/16's findings; the 6th VM remains dead since its `2026-08-06T17:09:47 UTC` `WORKER_STALLED` self-delete.
  `GET /api/backlog` confirms `-003` `status: dispatched, dispatched_to: 10`, priority 20;
  `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` confirmed still 3/5 done via direct grep (`-004`/`-005` both
  `[ ]`, unchanged). Gate ("genuinely completes, measured exit") remains unmet.

  **Root-caused the `-007` (7th-relaunch INFRA todo) all-day stall — new finding, not just another "still un-picked-up"
  count.** `GET /api/backlog` on `-007` shows `target_slot: 4, affinity: "high"` — per RULES.md § "Slot affinity",
  `affinity: high` means ONLY slot 4 can ever claim it, every other slot skips past indefinitely. `GET /api/state` on
  slot 4: `worker_alive: false`, `tmux_alive: false`, `status/phase: idle`, and critically `last_spawned_at`
  (`2026-08-08T18:25:35Z`) is AFTER `last_ping` (`2026-08-08T18:19:58Z`) — i.e. slot 4 was respawned and has never
  successfully booted/pinged since. `-007` is bound to a slot that cannot currently claim anything; it was never being
  "missed" by the fleet, it is structurally undispatchable until slot 4 comes back alive or the binding is cleared. This
  is consistent with RULES.md's documented Reassign-endpoint behavior (`target_slot=<self>, affinity=high` is the
  DEFAULT when a slot calls `/reassign` on its own task) — plausible that slot 4 self-reassigned `-007` to itself at
  some point today, then died before claiming it, orphaning the binding. Posted to role=main
  (`/api/agents/by-role/main/message`, msg id 4338) recommending either a force-respawn of slot 4 or a
  `/api/slots/<live-infra-slot>/reassign` to rebind `-007` to a live slot — this is a backlog-tuning action, main/
  operator-only per RULES.md § "Backlog-edit hygiene", not something a review-craft dispatch can hand-apply. Declining
  todo `-003` and skipping via `reason_code: "GATED"` per the established pattern — the VM-completion gate itself is
  unchanged, but the `-007` root-cause finding is new and actionable for whoever reads this next.

- 2026-08-08T20:22Z (slot-23, review craft — adopted per per-task craft rule, dispatched on todo `-003`): Independent
  re-verify (8th dispatch today): `gcloud compute instances list --filter="name~cefi-queue"` → empty; broader
  `name~cefi` shows 5 live `cefi-*` VMs (`cefi-fwd-…`, `mdps-backfill-cefi-…` ×2, `mdps-features-live-cefi-…`,
  `mtds-live-cefi-consolidated-…`), none matching `cefi-queue-*` — confirms the 6th VM remains dead since its
  `2026-08-06T17:09:47 UTC` `WORKER_STALLED` self-delete; no 7th relaunch exists yet. `GET /api/backlog` confirms `-003`
  `status: dispatched, dispatched_to: 23`, priority 20; `-007` (7th-relaunch INFRA todo) still
  `status: queued, dispatched_to: None, target_slot: 4, affinity: high`. Re-checked slot-10's root-cause finding
  directly: `GET /api/state` on slot 4 → `status: killed, worker_alive: false, tmux_alive: false, phase: killed`,
  `last_spawned_at: 2026-08-08T20:17:21Z` (a further respawn attempt since slot-10's 18:25Z snapshot) with `last_msg`
  showing it resumed an UNRELATED task (`sports_taxonomy_p1_capture_and_contracts-020`) — slot 4 has been respawned at
  least twice since orphaning `-007`'s binding and is dead again now, so the stuck `affinity: high` binding on `-007`
  remains unresolved; slot-10's msg 4338 recommendation to main (force-respawn slot 4 or reassign `-007` off it) has not
  yet been actioned ~2h later. `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` confirmed still 3/5 done via
  direct grep (`-004`/`-005` both `[ ]`, unchanged). Gate ("genuinely completes, measured exit") remains unmet — not
  re-pinging main (slot-10's still-fresh, un-actioned ping already covers it; a 2nd ping this soon adds no new
  information). Declining todo `-003` and skipping via `reason_code: "GATED"` per the established pattern.

- 2026-08-08T21:31Z (slot-22, review craft, dispatched on todo `-003`): Independent re-verify (9th dispatch today) —
  **the `-007` stall is resolved: a 7th relaunch VM is now RUNNING.**
  `gcloud compute instances list --filter="name~cefi-queue"` → `cefi-queue-heavy-binancefutu-x17-20260808-213038`
  RUNNING, `asia-northeast1-c`. `gcloud compute instances describe` confirms `scheduling.provisioningModel=STANDARD`
  (ON_DEMAND, not SPOT — continuing the operator's 2026-08-06 option-(b) ruling) and `creationTimestamp` =
  `2026-08-08T14:30:47-07:00` (= `21:30:47 UTC`) — i.e. the VM is **~1 minute old** at check time (`21:31:37 UTC`), no
  `PROGRESS.json`/`run.log` published yet (too early — `gcloud storage cat` on both returned no-match, expected for a VM
  this fresh, not a failure signal). `GET /api/backlog` confirms `-007`
  `status: dispatched, dispatched_to: 21, target_slot: 8, affinity: high` — no longer stuck on the dead slot-4 binding
  slot-10/slot-23 flagged (target_slot moved 4→8 and a live slot claimed it), so main/operator appears to have actioned
  the reassignment recommendation. `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` confirmed still 3/5 done
  via direct grep (`-004`/`-005` both `[ ]`, unchanged). Gate (`-003`'s "genuinely completes, measured exit") remains
  unmet — a VM 1 minute into a ~2769-day-scope backfill is nowhere near completion. Declining todo `-003` and skipping
  via `reason_code: "GATED"` per the established pattern. Worth noting for the next dispatch: this is finally a LIVE,
  freshly-launched VM again after the 6th VM's `2026-08-06T17:09:47 UTC` death — check its `PROGRESS.json` (should exist
  within a few minutes) rather than assuming another all-day stall.

- 2026-08-08T21:41Z (slot-21, infra craft, dispatched on todo `-007`): Completed todo `-007` (7th relaunch). Before
  relaunching, investigated the WORKER_STALLED root cause per the todo's own instruction rather than blind-relaunching.
  Found the dead 6th VM's `LAUNCH_PARAMS.json` carried `TARDIS_CONCURRENCY_LEASE=1` with no `STALL_TIMEOUT_SEC`
  override, launched while a concurrent `cefi-fwd-*` VM held the workspace-wide Tardis lease.
  `tardis_concurrency_lease_max_wait_seconds` (MTDS `service_config.py`) defaults to exactly 1800s — the SAME default as
  the shell watchdog's `STALL_TIMEOUT_SEC` — so the lease-acquire blocking wait (zero log output the whole time) and the
  watchdog's own 1800s no-progress timer raced on identical clocks; the watchdog won at 1841s. This is precisely the
  2026-07-14 incident pattern `launch-cefi-sharded-backfill.sh`'s own comment already documented ("For lease-ON launches
  into a busy fleet set e.g. 3900") but never enforced as a default — a caller had to remember it. Separately, confirmed
  the stall-kill diagnostic itself was useless on every prior occurrence in this chain: `CMD_PID` is always the outer
  bash chunk-loop wrapper, which is blocked in `wait()` for its own children whenever the command is alive at all, so a
  py-spy/`/proc` stack dump of `CMD_PID` alone shows only `do_wait` regardless of what the real python worker is stuck
  on (confirmed against every prior WORKER_STALLED entry in this doc — none ever showed anything but `do_wait`).

  Shipped 2 fixes, both QG-verified + quickmerged to `live-defi-rollout`:
  - `deployment-service@78da8126` — stall-dump now walks every descendant PID of `CMD_PID` (via `pgrep -P`, 6 levels
    deep) and dumps each live one via py-spy/`/proc` stack instead of just `CMD_PID`, so the next stall is actually
    diagnosable.
  - `deployment-service@f735ff23` — both `launch-cefi-sharded-backfill.sh` metadata-building paths (the per-shard
    direct-launch path and the `SINGLE_VM_QUEUE` flush path the 6th VM actually used) now auto-default
    `STALL_TIMEOUT_SEC=3900` whenever `TARDIS_CONCURRENCY_LEASE=1` is set and the caller hasn't passed an explicit
    override — turning the 2026-07-14 comment's advice into an enforced default. An explicit caller override still wins
    (verified via an isolated 3-case snippet test: lease-on/no-override→3900, lease-off→unchanged,
    lease-on/explicit→respected).

  7th relaunch: `cefi-queue-heavy-binancefutu-x17-20260808-213038` (`asia-northeast1-c`, ON_DEMAND/STANDARD — continuing
  the operator's 2026-08-06 option-(b) ruling, not SPOT; `FORCE=1` Tardis-cap override, same justification as the 6th VM
  since `cefi-fwd-20260808-123230` was still running; scope `2019-01-01..2026-08-07`, 17 venues, `heavy`/
  `trades;book_snapshot_5`, reproducing the 6th VM's `LAUNCH_PARAMS.json` env with no `START_DATE` override so the
  manifest-driven skip-if-fresh fast-forwards through the ~295 already-captured days). Also passed
  `MACHINE_TYPE_HEAVY=e2-highmem-16` explicitly (same value the unset default already resolves to) purely to SKIP
  `registry_machine_floor()`'s per-venue-iteration python-subprocess call in the queue-build loop — noticed this because
  the FIRST launch attempt (no override) took >20s/venue-year and was killed by a background-task duration ceiling
  before ever reaching VM creation (confirmed via `gcloud compute operations list` — no insert op existed); the override
  made the identical queue build finish in under a minute with the same resulting VM. Not fixing
  `registry_machine_floor()`'s per-iteration subprocess cost now (out of this todo's scope) — flagging it here as a
  real, reproducible slowness finding for a future follow-up.

  **Verified, not just launched**: `gcloud compute instances describe` → `RUNNING`, `provisioningModel=STANDARD`.
  `LAUNCH_PARAMS.json` for the new VM confirms `STALL_TIMEOUT_SEC=3900` actually landed (not just present in source).
  `PROGRESS.json` genuinely advancing: `{"last_completed_date":"2019-02-11","monotonic":true,...}` at chunk 6/397, ~4
  min after creation, `run.log` showing live `ServiceRuntime`/`ResourceProfiler` output, not idle. Independently
  cross-confirmed by slot-22's `-003` re-verify entry above (same VM, same RUNNING state, filed concurrently). `-003`
  (POST-BACKFILL gate) remains correctly gated — a VM minutes into a ~2769-day scope is nowhere near completion; not
  touching it. Repo: deployment-service.

- 2026-08-08T22:40Z (slot-26, review craft — adopted per per-task craft rule, dispatched on todo `-003`): Independent
  re-verify (10th dispatch today): `gcloud compute instances list --filter="name~cefi-queue"` →
  `cefi-queue-heavy-binancefutu-x17-20260808-213038` `RUNNING`, `asia-northeast1-c`,
  `scheduling.provisioningModel=STANDARD` (ON_DEMAND, continuing the operator's 2026-08-06 option-(b) ruling),
  `creationTimestamp=2026-08-08T14:30:47-07:00` (= `21:30:47 UTC`) — ~1h9min old at check time (`22:40:02 UTC`).
  `PROGRESS.json` → `{"last_completed_date":"2020-04-13","monotonic":true,"updated":"2026-08-08T22:39:33Z"}` — genuinely
  advancing (matches slot-21's chunk-6/397 reading ~1h earlier at `2019-02-11`), now ~day 469/2769 (~17%) of the
  `2019-01-01..2026-08-07` scope, mostly the manifest-driven skip-if-fresh fast-forwarding through the ~295+ days
  already captured by relaunch attempts 1-6 — real new-work progress rate is much lower than the raw date-jump suggests.
  `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` confirmed still 3/5 done via direct grep (`-004`/`-005` both
  `[ ]`, unchanged). Gate (`-003`'s "genuinely completes, measured exit") remains unmet — a VM ~17% through a ~2769-day
  scope, with no terminal exit yet, is not a completion. `GET /api/backlog` confirms `-003`
  `status: dispatched, dispatched_to: 26`, priority 20, no `prereqs` — not currently auto-parked. Declining todo `-003`
  and skipping via `reason_code: "GATED"` per the established pattern (slot-13's mechanism finding, 2026-08-02). Not
  filing a fresh chat-to-main ping — nothing new to report beyond continued genuine progress on the 7th (ON_DEMAND) VM,
  which slot-21/slot-22 already surfaced ~1h ago.

- [x] ✅ [INFRA] P1. **DONE 2026-08-09 (slot-29, infra craft)** — Fixed `STALL_PROGRESS_REGEX` (defaulted to `uploaded`,
      never matching honest-absence stretches → false stalls). Broadened to `uploaded|Processed date=`, mirroring the
      mdps launcher's `Processing|Skipping` precedent. Repo: deployment-service@8095aeba. Moved the per-shard metadata
      path's pair-delimiter `|`→`~` (else the new literal `|` in the regex value collides with it); comma-delimited
      `SINGLE_VM_QUEUE` path unchanged. Verified via `bash -n`/`shellcheck` + a standalone simulation + one pre-commit
      `quality-gates.sh` pass (all substantive gates ✅; only the 700s>600s wall-clock META-gate failed,
      `IGNORE_TIMEOUT=true` rerun clean). **Shipped via the operator-approved `scripts/**` direct-push carve-out
      (D16)**: post-commit host hit a severe incident (load ~40→69, 19 concurrent QGs vs ≤2 cap) killing 9 QG attempts
      via the RAM watchdog; filed `/blocked` (BLK-426dd60f), operator approved (msg 6203). Verified `8095aeba` on
      origin. Did NOT relaunch the VM — tracked as its own follow-up todo below.

- 2026-08-09T00:24Z (slot-4, review craft, dispatched on todo `-003`): Independent re-verify. 7th VM
  (`cefi-queue-heavy-binancefutu-x17-20260808-213038`) died: `insert` 21:31:06 UTC, `delete` 22:42:15 UTC (no
  `preempted` op — ON_DEMAND). run.log: `WORKER_STALLED (no-progress-marker) stalled_for=3936s (threshold=3900s)` at
  `date=2020-04-14`, despite continuous `Processed date=` advances every ~~7-10s right up to the kill and
  `PROGRESS.json` last write `2020-04-13`/day~~469/2769 (~17%) — NOT a genuine hang. **New root cause**:
  `STALL_PROGRESS_REGEX` defaults to literal `uploaded` — grep confirms it appears exactly once in the whole 5421-line
  run.log (the boilerplate header), because the VM's `2020-03-20..2020-04-14` stretch is honest-absence (0 instruments
  across all venues, nothing to upload). `made_progress` in `vm-exec-with-gcs-tee.sh` never fired once during that
  stretch, so the watchdog just timed out from VM-boot. Distinct from the 6th VM's lease-race cause — every other
  launcher (e.g. `launch-mdps-sharded-backfill.sh`) regexes a per-item advance marker, not a write-only one; cefi's
  default is the outlier. Filed `[INFRA] P1` todo above (8th relaunch, fix-first).
  `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` confirmed still 3/5 (`-004`/`-005` `[ ]`). Gate unmet —
  declining `-003` via `reason_code: "GATED"`.

- 2026-08-09T01:47Z (slot-25, review craft, dispatched on todo `-003`): Independent re-verify.
  `gcloud compute instances list --filter="name~cefi-queue"` → empty, no `cefi-queue-*` coverage-backfill VM running
  (the 7th VM's replacement has not launched yet). `GET /api/backlog` on the 8th-relaunch `[INFRA]` fix-first todo
  (`cefi_track2_backfill_vm_preempted_no_recovery-99a54eb412aa`, the `STALL_PROGRESS_REGEX` fix) →
  `status: dispatched, dispatched_to: 29, done_sha: null` — still in-flight on slot-29, not yet shipped, so the relaunch
  this gate needs hasn't happened. `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` confirmed still 3/5 done
  (`-004`/`-005` both `[ ]`, unchanged). Gate (`-003`'s "genuinely completes, measured exit") remains unmet. Declining
  `-003` and skipping via `reason_code: "GATED"` per the established pattern — no new mechanism finding to add this
  round; slot-29 finishing the regex fix + relaunching is the next real state change to watch for.

- [x] ✅ [INFRA] P1. **DONE 2026-08-09 (slot-17, infra craft)** — 8th relaunch. Repo: deployment-service (relaunch only;
      launcher unchanged from `8095aeba`). N=1 Tardis cap confirmed clear both clouds (`tardis_running_vm_count`=0; AWS
      only standing VMs). Reproduced 7th VM's `LAUNCH_PARAMS.json` verbatim via
      `launch-cefi-sharded-backfill.sh --on-demand` → `cefi-queue-heavy-binancefutu-x17-20260809-083733`
      (`2019-01-01..2026-08-08`, 17 venues). Verified metadata carries the fix
      (`STALL_PROGRESS_REGEX=uploaded| Processed date=`, `STALL_TIMEOUT_SEC=3900`). RUNNING@T+1min; `PROGRESS.json`
      polled every 2min over a 14min watch, monotonic `2019-05-06→2019-07-29` (day~126→210), well past the
      `~day-119/469` point where the 3rd/7th VMs false-stalled. No stall/preemption across the watch. `-003` remains
      correctly blocked (VM ~7.6% through scope) — not touching it.

- 2026-08-09T03:19Z (slot-29, infra craft): Shipped the fix-first todo (`deployment-service@8095aeba`); filed the
  relaunch as its own todo (out of this task's scope) — `-003` gates on it now.

- 2026-08-09 (slot-20, review craft, dispatched on todo `-003`): Independent re-verify.
  `gcloud compute instances list --filter="name~cefi-queue"` → empty — 8th relaunch (`-a98bd95ca7c7`) not yet launched,
  `dispatched` to slot 17. `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` confirmed still 3/5 (`-004`/`-005`
  `[ ]`). Gate unmet — declining `-003` via `reason_code: "GATED", park_now: true` (per `-99a54eb412aa`'s
  stalemate-mechanism finding, 2026-08-02) to stop the redispatch churn until the 8th relaunch genuinely completes.
- 2026-08-09T08:43Z (slot-28, review): 8th VM `...20260809-083733` RUNNING (ON_DEMAND, `STALL_TIMEOUT_SEC=3900` +
  `STALL_PROGRESS_REGEX` fixes both confirmed live). `PROGRESS.json` day~42/2769 (~1.5%), genuine advance, no false
  HONEST_ABSENCE stall. `-004`/`-005` still `[ ]`. Gate unmet — declining `-003` via `GATED, park_now: true`.

- 2026-08-09T09:00Z (slot-17, infra craft): Completed the 8th-relaunch todo — full evidence in the flipped todo above.
  8th distinct relaunch of this chain, 2nd to genuinely survive past the historical false-stall point. Whoever next
  checks `-003` should watch for continued advance or a NEW failure mode (the 2 known classes — lease-race,
  honest-absence false-stall — are both now fixed).
