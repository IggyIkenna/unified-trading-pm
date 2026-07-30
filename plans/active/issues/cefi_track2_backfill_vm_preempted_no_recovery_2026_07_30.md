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
      Repo: unified-trading-pm.

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
