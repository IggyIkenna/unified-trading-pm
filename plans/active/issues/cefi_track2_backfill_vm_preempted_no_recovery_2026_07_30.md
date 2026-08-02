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
parent_epic: cefi_master
priority: P1
source: ["finalize-001 (slot 10, review craft) reconciliation task, 2026-07-30"]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-30
locked_since:
context_scope:
  [
    /plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md,
    /plans/active/cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
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

- 2026-07-30 (slot-10, review craft): Picked up todo 3 again (re-run POST-BACKFILL gate once the relaunch genuinely
  completes). Independently re-verified before declining:
  `gcloud compute instances describe cefi-queue-heavy-binancefutu-x17-20260730-193717` → still `RUNNING` (SPOT) — the
  3rd relaunch has NOT preempted again. `PROGRESS.json` confirms the checkpoint mechanism is genuinely live and
  advancing: `{"last_completed_date":"2020-01-28","monotonic":true,"updated":"2026-07-30T19:57:05Z"}`. `run.log` tail
  (19:58-19:59 UTC) shows continued real progress past that point into `date=2020-02-01`/`2020-02-02`, mostly via fast
  pre-flight skip-ahead through venues already fully covered from earlier historical runs
  (`RESOURCE_SAMPLE cpu=99.9-100.2% rss=~4.8-4.9GiB` confirms genuine compute, not a hung/idle VM). Still nowhere near
  completion: the VM's own scope is `VM_START_DATE=2020-01-01`/`VM_END_DATE=2026-07-29` and current position is only
  `2020-02-02` — the gate this todo waits on ("genuinely completes, measured exit") is still unmet.
  `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` confirmed still 3/5 done (`-004`/`-005` both still `[ ]`,
  unchanged). Declining todo 3 and skipping this task rather than holding the slot for what could be a
  multi-day-to-completion backfill, per the same posture as the 2026-07-30 slot-7/slot-9 entries above.

- 2026-07-30 (slot-13, review craft): Picked up todo 3 (`-003`) again. Independently re-verified before declining:
  `gcloud compute instances describe cefi-queue-heavy-binancefutu-x17-20260730-193717 --zone=asia-northeast1-c` →
  `RUNNING` (SPOT) — the 3rd relaunch has NOT preempted again since slot-10's last check. `PROGRESS.json` confirms the
  checkpoint mechanism is genuinely live and advancing:
  `{"last_completed_date":"2020-02-04","monotonic":true,"updated":"2026-07-30T20:01:07Z"}`. `run.log` tail (20:03 UTC)
  shows continued real progress into `date=2020-02-08` (Tardis streaming successes across multiple venues,
  `RESOURCE_SAMPLE cpu=736.9% rss=3993MiB` — genuine compute, not a hung/idle VM). Still nowhere near completion: the
  VM's own scope is `VM_START_DATE=2020-01-01`/`VM_END_DATE=2026-07-29` (~2372 days) and current position is only
  `2020-02-08` — the gate this todo waits on ("genuinely completes, measured exit") is still unmet.
  `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` confirmed still 3/5 done (`-004`/`-005` both still `[ ]`,
  unchanged). Declining todo 3 and skipping this task rather than holding the slot for what remains a multi-day (at
  measured ~3.25 days/hr throughput, ~30-day wall-clock) backfill, per the same posture as the 2026-07-30
  slot-7/slot-9/slot-10 entries above.

- 2026-07-30 (slot-3, review craft): Picked up todo 3 (`-003`) again. Independently re-verified before declining:
  `gcloud compute instances describe cefi-queue-heavy-binancefutu-x17-20260730-193717 --zone=asia-northeast1-c` → still
  `RUNNING` (SPOT) — no further preemption since slot-13's last check. `PROGRESS.json` confirms continued advance:
  `{"last_completed_date":"2020-02-25","monotonic":true,"updated":"2026-07-30T21:26:13Z"}`. `run.log` tail
  (`21:59-22:01 UTC`) shows genuine live Tardis-streaming activity at `day=2020-03-03` (multiple venues — KRAKEN-SPOT,
  OKX-SWAP, BITFINEX-SPOT — each writing real parquet shards with hundreds-of-thousands of rows), confirming real
  compute, not a hung/idle VM. Still far from completion: target scope is `VM_START_DATE=2020-01-01`/
  `VM_END_DATE=2026-07-29` and current position is only `2020-03-03` — the gate this todo waits on ("genuinely
  completes, measured exit") is still unmet. `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` confirmed still
  3/5 done (`-004`/`-005` both still `[ ]`, unchanged). Declining todo 3 and skipping this task rather than holding the
  slot for a multi-day backfill, per the same posture as the 2026-07-30 slot-7/slot-9/slot-10/slot-13 entries above.

- 2026-07-31 (slot-12, review craft): Picked up todo 3 (`-003`) again. Independently re-verified before declining:
  `gcloud compute instances describe cefi-queue-heavy-binancefutu-x17-20260730-193717 --zone=asia-northeast1-c` → still
  `RUNNING` (SPOT) — no further preemption since slot-3's last check. `PROGRESS.json` confirms continued advance:
  `{"last_completed_date":"2020-03-31","monotonic":true,"updated":"2026-07-31T00:35:26Z"}`. `run.log` tail (`00:55 UTC`)
  shows genuine live Tardis-streaming activity at `day=2020-04-03` (OKX-SWAP/OKX-FUTURES writing real parquet shards,
  hundreds-of-thousands of rows each), confirming real compute, not a hung/idle VM. Still far from completion: target
  scope is `VM_START_DATE=2020-01-01`/`VM_END_DATE=2026-07-29` (~2372 days) and current position is only `2020-04-03`
  (~day 93 of ~2372) — the gate this todo waits on ("genuinely completes, measured exit") is still unmet.
  `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` confirmed still 3/5 done (`-004`/`-005` both still `[ ]`,
  unchanged). Declining todo 3 and skipping this task rather than holding the slot for a multi-day backfill, per the
  same posture as the 2026-07-30 slot-7/slot-9/slot-10/slot-13/slot-3 entries above.

- 2026-07-31 (slot-2, review craft): Picked up todo 3 (`-003`) again. Independently re-verified before declining:
  `gcloud compute instances describe cefi-queue-heavy-binancefutu-x17-20260730-193717 --zone=asia-northeast1-c` → still
  `RUNNING` (SPOT) — no further preemption since slot-12's last check. `PROGRESS.json` confirms continued monotonic
  advance: `{"last_completed_date":"2020-04-14","monotonic":true,"updated":"2026-07-31T02:53:32Z"}`. `run.log` tail
  (`03:01 UTC`) shows genuine live Tardis-streaming activity processing `date=2020-04-15` across 7 venues (136,781,111
  total records so far), plus `RESOURCE_SAMPLE cpu=100.1-100.2% rss=4.6-9.1GiB` — real compute, not a hung/idle VM.
  Still far from completion: target scope is `VM_START_DATE=2020-01-01`/`VM_END_DATE=2026-07-29` (~2372 days) and
  current position is only `2020-04-15` (~day 106 of ~2372, ~4.5%) — the gate this todo waits on ("genuinely completes,
  measured exit") is still unmet. `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` confirmed still 3/5 done
  (`-004`/`-005` both still `[ ]`, unchanged). Declining todo 3 and skipping this task rather than holding the slot for
  a multi-day backfill, per the same posture as the 2026-07-30/31 slot-7/slot-9/slot-10/slot-13/slot-3/slot-12 entries
  above.

- 2026-07-31 (slot-14, review craft): Picked up todo 3 (`-003`) again. Independently re-verified before declining:
  `gcloud compute instances describe cefi-queue-heavy-binancefutu-x17-20260730-193717 --zone=asia-northeast1-c` → still
  `RUNNING` (SPOT) — no further preemption since slot-2's last check. `PROGRESS.json` confirms continued monotonic
  advance: `{"last_completed_date":"2020-04-21","monotonic":true,"updated":"2026-07-31T04:03:35Z"}`. `run.log` tail
  (`04:07 UTC`) shows genuine live Tardis-streaming activity processing `date=2020-04-22` across multiple venues
  (OKX-FUTURES/OKX-SWAP writing real parquet shards, hundreds-of-thousands of rows each), plus
  `RESOURCE_SAMPLE cpu=279.1% rss=4151MiB` — real compute, not a hung/idle VM. Still far from completion: target scope
  is `VM_START_DATE=2020-01-01`/`VM_END_DATE=2026-07-29` (~2372 days) and current position is only `2020-04-22` (~day
  113 of ~2372, ~4.8%) — the gate this todo waits on ("genuinely completes, measured exit") is still unmet.
  `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` confirmed still 3/5 done (`-004`/`-005` both still `[ ]`,
  unchanged). Declining todo 3 and skipping this task rather than holding the slot for a multi-day backfill, per the
  same posture as the 2026-07-30/31 slot-7/slot-9/slot-10/slot-13/slot-3/slot-12/slot-2 entries above.

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

- [ ] [INFRA] P1. 5th relaunch of the cefi coverage-backfill VM after the 4th VM
      (`cefi-queue-heavy-binancefutu-x17-20260801-120637`) died via a DIFFERENT failure mode this time — a
      `WORKER_STALLED (no-progress-marker)` watchdog kill (exit_code=137) at `2026-08-01T12:40:27Z`, not a SPOT
      preemption (`gcloud compute operations list` for this instance shows only `insert`/`delete`, no `preempted` op —
      the VM self-deleted per `VM_SHUTDOWN_ON_COMPLETION=true` after the watchdog killed the stalled worker). Reached
      only `date=2020-02-17` of the `2020-01-01..2026-07-31` span (~48/2373 days, ~2%) before stalling — the run.log
      shows a `SHARD_INCOMPLETE`/`0 venues ok` pattern for the date it stalled on, consistent with a hung per-venue
      fetch rather than a clean day-boundary stop. Dead for ~27h with no replacement launched as of this entry. Repo:
      deployment-service (relaunch action; the stall cause itself may warrant separate root-cause investigation but is
      not blocking a relaunch — the watchdog's own stall-kill + self-delete already returned the host cleanly).

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
