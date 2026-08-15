---
doc_type: issue
title:
  "A VM relaunched under a NEW name cannot resume from a prior VM's PROGRESS.json checkpoint — re-walks from START_DATE"
summary: >-
  Distinct from cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md (which covers PROGRESS.json not being
  WRITTEN at all for a launcher family, now fixed via deployment-service@28b7dce) — this is about a launcher that DOES
  write PROGRESS.json correctly, but a manual relaunch after the original VM dies (**CORRECTED 2026-08-14: confirmed
  ordinary SPOT preemption, not an OOM-class kill — see below**) creates a NEW VM with a new name/log path, which has no
  mechanism to read the DEAD VM's checkpoint file. Net effect: the relaunch silently re-walks from the original
  START_DATE instead of resuming from the last completed date, wasting real API calls/wall-clock (idempotent re-fetch,
  not data-corrupting, but a real cost this workspace's own resume-checkpoint contract is supposed to prevent).
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [deployment-service, market-tick-data-service]
scope: [engineer, admin]
tags: [vm-launcher, spot-preemption, resume-checkpoint, billing-waste]
related:
  [
    /plans/active/issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
  ]
parent_epic: cefi_master
source:
  "CeFi equity-perp Tardis backfill, 2026-08-12 interactive session — cefi-okx-swap-2026-heavy VM died silently mid-run
  (no exit_code/traceback/preemption marker in the log; confirmed 2026-08-14 as ordinary SPOT preemption via full
  resource-sample history, not OOM), manual relaunch under a new VM name confirmed re-walking already-captured dates"
assigned_vm: NA
created: 2026-08-12
resolved_by:
locked_by:
locked_since:
priority: P2
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /plans/active/issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md,
  ]
---

# VM relaunch under a new name cannot resume from a prior VM's checkpoint

## CORRECTED 2026-08-14 — death cause resolved: ordinary SPOT preemption, not OOM

> **CORRECTION.** The original finding below characterized the RSS trajectory right before death (17.7GB→51GB in <4min)
> as an unexplained runaway. That read only looked at the LAST few `RESOURCE_SAMPLE` lines before the log went silent.
> Pulling the FULL resource-sample history for both OKX-SWAP VMs (449 + 1,436 samples) and, separately, both
> BINANCE-FUTURES cohortA-heavy VMs from the very next backfill run (149 + 804 samples — ~2,838 samples total across 4
> independent VM deaths) shows this is a clean, repeating, BOUNDED sawtooth: climbs from ~2-6GB to ~55-68GB over 5-7
> minutes (one calendar day's fan-out for this shard's instrument set), then drops back to ~2-7GB once that day writes
> and releases — never a monotonic runaway. Every one of the 4 deaths happened at essentially random points in that
> cycle, including one at only 28.7% of the machine's 128GB ceiling — nowhere near a peak, let alone the ceiling. The
> launcher's own wrapper (`setup-data-pipeline-vm.sh`'s `CEFI_CHUNK_SCRIPT`) explicitly detects a child OOM-kill (exit
> 137 → logs `CHUNK_FAILED: ... reason=OOM_KILLED`) and that line appears **zero times** across all 4 run.logs. The logs
> just stop instantly with no wrapper-level message either — consistent with the WHOLE VM (wrapper included)
> disappearing at once, i.e. genuine SPOT reclaim, not the Python process being individually OOM-killed while the
> wrapper survives to log it. **Verdict: this launcher's "heavy" tier has no memory leak and no OOM risk at its current
> scope** — the silent deaths are ordinary, expected SPOT preemption. Answers the P3 todo below.

## What was found (2026-08-12)

`cefi-okx-swap-2026-heavy-20260812-225944` (a `launch-cefi-sharded-backfill.sh` VM) correctly processed 2026-02-25
through 2026-04-14 (`PROGRESS.json: last_completed_date=2026-04-14, monotonic=true`), each day logging real captured
trades+book_snapshot_5 rows. It then died silently while processing 2026-04-19 — the log stops entirely: no
`exit_code=`, no traceback, no SIGTERM/SIGKILL marker, no preemption event anywhere in the log. `gcloud describe` 404s
on the instance — genuinely gone, not just stopped. **Cause now confirmed** (see correction above): ordinary SPOT
preemption, not an OOM-class kill.

A manual relaunch (`cefi-okx-swap-2026-heavy-20260813-120003`, same scope) was confirmed genuinely running, but
**re-processed 2026-02-25 from scratch** rather than resuming at 2026-04-15 — the new VM has its own name and GCS
log/checkpoint path, with no mechanism to discover or read the dead VM's `PROGRESS.json`. Separately,
`MANIFEST_CONSOLIDATED_STALENESS_SEC=86400` means the manifest reader tolerates a same-day-stale consolidated index, so
the relaunch also doesn't see the first VM's already-captured shards via that path either.

**Cost**: not data-corrupting (re-fetching real data is idempotent), but real, avoidable waste — ~49 already-captured
days re-walked (real Tardis API calls + wall-clock) before reaching new territory.

## Todos

- [ ] [INFRA] P2. Give `launch-cefi-sharded-backfill.sh` (and any sibling launcher using the same per-VM-named
      `PROGRESS.json` pattern) a way for a manual/auto relaunch to discover and resume from the PRIOR VM's checkpoint
      for the same logical job (same venue/scope/date-range) — e.g. a stable job-id-keyed checkpoint path independent of
      the VM's own instance name, or an explicit `--resume-from-vm=<prior-vm-name>` flag that reads that VM's
      `PROGRESS.json` before starting. Mirrors the intent already proven for SPOT-preemption auto-relaunch
      (`spot-vms-for-backfill.md`'s resume-checkpoint contract) — this closes the gap for a MANUAL relaunch under a
      genuinely new name, which the auto-relaunch path may not hit the same way.
- [x] ✅ [INFRA] P3. **ANSWERED 2026-08-14 — confirmed SPOT preemption, not OOM; rightsizing checked, no action
      needed.** See correction above for the full evidence (4 VM deaths, ~2,838 combined RESOURCE_SAMPLE lines, 0
      OOM_KILLED lines). Separately ran `/vm-resource-rightsizing-check` on the current `e2-highmem-16` default: CPU is
      genuinely underutilized (~100% of 16 vCPU ≈ 6-7%, matching the 2026-08-10 tradfi audit's signature) but this is
      NOT a fixable over-provisioning case — GCP hard-caps every custom machine family (e2, n2) at 64GB for an 8-vCPU
      shape (`gcloud compute machine-types describe` confirms this directly), and this shard's peak (~55-68GB) already
      exceeds that, so 16 vCPU is the actual GCP-enforced MINIMUM to hold the current working set — there is no smaller
      shape that keeps the same RAM. The real idle-capacity lever is `--batch-date-concurrency` (parallelizing dates
      within a chunk, default OFF) — NOT recommended yet: it would run multiple currently-uncapped ~60GB per-date peaks
      concurrently, and the shared `ParallelPerSymbolRunner` path this launcher uses has a confirmed, still-open gap
      (`mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`'s P2: `max_in_flight_bytes` is permanently `None`, a
      no-op) — enabling concurrency before that lands would knowingly reproduce the OOM history already documented there
      for the sibling sports/odds_api launcher. Fix that P2 first, then revisit concurrency as a throughput win.
- [ ] [CODE] P3. **NEW (found 2026-08-15).** `launch-cefi-sharded-backfill.sh`'s year-scoping env var is a real footgun:
      the script's OWN usage comment (line 677) documents `YEARS="2024"` as the override, and internally assigns
      `YEARS_OVERRIDE="${YEARS:-}"` (line 681) — but `YEARS_OVERRIDE` is also the name of that internal working
      variable, so a caller who (reasonably) exports `YEARS_OVERRIDE=2026` directly gets it silently stomped back to
      empty by line 681, falls through to the venue's full default year range, and then fails
      `START_DATE='...' must be YYYY-MM-DD within year <first-default-year>` — this is confirmed live-reproduced as the
      root cause of this doc's own still-open P2's repeated failed relaunch attempts (see 2026-08-15 Progress Log entry
      below). Fix: rename the internal variable to something that doesn't collide with a plausible-but-wrong env var
      name (e.g. `_YEARS_SCOPE`), or add an explicit `[[ -n "${YEARS_OVERRIDE:-}" && -z "${YEARS:-}" ]]` guard that
      errors loudly ("did you mean YEARS=?") instead of silently discarding the caller's intent.

## Progress Log

- 2026-08-12 — Filed. RSS-trajectory tail-read led to an OOM-vs-preemption open question (P3).
- 2026-08-14 — Investigating a live BINANCE-FUTURES cohortA-heavy stall (separate `/vm-preemption-billing-waste-audit`
  - `/vm-resource-rightsizing-check` pass, prompted by an operator ask to check VM memory/CPU usage properly rather than
    "just advocate more resources") pulled the FULL resource-sample history for that run too, which contradicted my own
    live read moments earlier in the same session (I'd initially, wrongly, pattern-matched a tail-only snapshot to this
    doc's OKX-SWAP finding). Re-checked THIS doc's original OKX-SWAP evidence the same way and found the identical
    tail-only mistake here. Corrected both P3 and the summary/body above; no code or data was affected by the wrong
    framing (it never drove any action beyond this doc's own open todo). Also closed the rightsizing half of the P3 todo
    the same session — see correction above for the full reasoning on why the CPU idleness isn't independently fixable.
- 2026-08-15 — Attempted the P2 relaunch (BINANCE-FUTURES cohortA-heavy, resume from the `2026-04-12` checkpoint left by
  `cefi-binance-futures-2026-heavy-20260815-002451`). Four findings:
  1. **Root cause of the intermittent `START_DATE=... must be YYYY-MM-DD within year 2020` failure, confirmed via
     `DRY_RUN=1`**: the caller must set `YEARS="2026"` (not `YEARS_OVERRIDE`, which is silently discarded — see the new
     [CODE] P3 todo above for the exact mechanism). The correct invocation, dry-run-verified to produce exactly 1 VM
     with `VM_START_DATE=2026-04-13 VM_END_DATE=2026-08-14`:
     `VENUES="BINANCE-FUTURES" YEARS="2026" ONLY="BINANCE-FUTURES:2026:heavy" START_DATE="2026-04-13" bash scripts/vm/launch-cefi-sharded-backfill.sh`.
  2. **A third, unexplained relaunch already ran and died before this check**:
     `cefi-binance-futures-2026-heavy- 20260815-143847` (`LAUNCH_PARAMS.json`: `ONLY=BINANCE-FUTURES:2026:heavy`, no
     `START_DATE`) ran ~14:38-15:04 UTC 2026-08-15, launched by something outside this conversation (this slot had a
     `SessionStart` collision warning for 10 other live `claude` processes sharing this cwd). Its `PROGRESS.json` shows
     `last_completed_date=2026-01-14` (worse than the existing `2026-04-12` checkpoint — it re-walked from `2026-01-01`
     because `START_DATE` was never set, exactly the still-open P2 gap this doc tracks) and its `WATCHDOG_TRACE.log`'s
     last heartbeat was 2.5h stale at check time — genuinely dead (ordinary silent SPOT preemption, `EXIT_STATUS` never
     updated past `RUNNING`, same signature as every death this doc already documents), not a live conflict. Confirmed
     via `gcloud compute instances list` returning zero matches before proceeding.
  3. **The real (parameterized-correctly) launch attempt aborted safely, no VM created, no cost**: the launcher detected
     `unified-api-contracts`'s deployed code tarball is stale and tried to auto-republish it, but refused because that
     repo has foreign uncommitted changes in this shared checkout (the same dependency-revocation /
     `flatten_readiness.py` WIP already blocking `tradfi_fx_krw_usd_phantom_rows_fresh_confirmation_2026_08_12.md`'s
     race-fix script ship — see that doc's matching 2026-08-15 entry). Did not pass `--allow-dirty-tarball` — that would
     deploy another session's unreviewed, uncommitted code onto a live production VM, not something to force
     unilaterally. **VM3 is now correctly parameterized and ready to fire the moment `unified-api-contracts` clears** —
     nothing else blocks it.
  4. **Portability note for whoever runs this launcher from a local macOS shell** (as opposed to the Linux AO
     orchestrator, where it's normally invoked): line 322's `date -u -d yesterday +%Y-%m-%d` is GNU-only syntax and
     fails outright on BSD/macOS `date`. Workaround: prepend a `gdate` (homebrew `coreutils`) shim onto `PATH` for the
     invocation, e.g. `ln -sf "$(which gdate)" <tmpdir>/date && PATH="<tmpdir>:$PATH" <launch command>`. Not filing this
     as its own todo — it only bites a local macOS invocation, which is not this launcher's normal path.
