---
doc_type: codex-ssot
title: Spot VMs for Backfill — the provisioning standard
summary:
  HARD-RULE provisioning standard — every backfill/idempotent VM launcher defaults to GCP Spot
  (--provisioning-model=SPOT --instance-termination-action=DELETE --no-restart-on-failure; ~60-91% cheaper), with
  --on-demand/ON_DEMAND=true the only opt-out and live/forward/cron/paper launchers staying on-demand.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [spot-vm, backfill, cost, infrastructure, deployment, runbook]
related:
  [
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
    /codex/05-infrastructure/deployment-observability.md,
    /codex/05-infrastructure/aws-migration-cost-snapshot-2026-05-07.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
  ]
created: 2026-06-27
authoritative_for: [Spot-VM provisioning standard for backfill launchers]
referenced_by:
  [
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
    plans/active/issues/terminated_vm_disk_orphan_no_reaper_2026_06_30.md,
  ]
owner:
last_reviewed: 2026-06-27
code_refs:
type: infrastructure
execution:
  {
    owner: deployment-platform,
    cadence: per VM-launcher add/change,
    verifier:
      rg -L 'provisioning-model=SPOT' deployment-service/scripts/vm/launch-*backfill*.sh (every backfill launcher must
      match),
    last_executed: 2026-06-27 (fleet-wide conversion),
  }
---

# Spot VMs for Backfill — the provisioning standard

> **HARD RULE.** Every **backfill / idempotent** VM launcher provisions GCP **Spot** VMs by default
> (`--provisioning-model=SPOT`). Spot is ~60–91% cheaper than on-demand. Backfill is idempotent (per-shard manifest
> resume via `VM_NAME` + `MANIFEST_PER_VM_SHARDS=true`), so a preempted shard re-runs cleanly — there is no correctness
> cost to preemption, only a restart. **On-demand for backfill is now a bug**, not a default.
>
> **"Re-runs cleanly" requires a relauncher — it is NOT automatic (corrected 2026-07-16, operator-approved).** The claim
> above was FALSE for the cefi/tardis launcher family until 2026-07-16: `--instance-termination-action=DELETE` +
> `--no-restart-on-failure` meant a preempted backfill VM was deleted and **nothing re-ran it** — the shard was
> idempotent in principle, but no actor invoked the re-run, so waves silently vanished (measured: 2 VMs preempted ~6 min
> into real work, 2026-07-15T22:05Z, with `exit_code_fleet_monitor` logging a `→ SPOT relaunch` that did not exist).
> **Now true for launchers that call `lc_write_launch_params()` at create time** (currently
> `launch-cefi-sharded-backfill.sh` + its AWS twin): the `exit_code_fleet_monitor` PREEMPTED verdict dispatches
> `RelaunchPreemptedVm` (`deployment-service/scripts/recovery/relaunch_backfill_vm.py`), which replays the captured
> launch env through the launcher's own `tardis_concurrency_guard` (so a relaunch can never breach the concurrency cap).
> A launcher that does NOT call `lc_write_launch_params()` still gets a best-effort relaunch attempt (ambient env only),
> **not** an exact-params replay — if you add a new backfill launcher, call `lc_write_launch_params()` or your preempted
> waves will not resume with their real scope. Shipped `deployment-service@02be72e6`; design + measured evidence:
> `plans/archive/2026_07/cefi_completion_program_2026_07_15.md` (2026-07-16).

## Why (the trigger)

GCP **promotional credits were exhausted ~2026-06-20** (verified in the BigQuery billing export: the `PROMOTION` credit
line went from ~$180/day on 2026-06-18 to **$0** by 2026-06-24). Before that, on-demand backfill was credit-covered (net
$0/day); after, the same fleet billed as **real cash** — a backfill spike hit **$2,513 net on 2026-06-24** alone. Spot
is the structural fix: it cuts the backfill compute bill ~60–91% regardless of credit state, and it keeps the GCP-vs-AWS
picture honest while the dual-cloud backfill finishes (see
[`aws-migration-cost-snapshot-2026-05-07.md`](aws-migration-cost-snapshot-2026-05-07.md)).

## The standard flag set

```bash
--provisioning-model=SPOT --instance-termination-action=DELETE --no-restart-on-failure
```

- **`--provisioning-model=SPOT`** (NOT legacy `--preemptible`): Spot has **no 24h forced-termination cap**, so heavy
  shards (multi-year CME/DEX OHLCV, e2-highmem) run to completion; they're interrupted only on real capacity pressure.
  `--preemptible` is deprecated — do not introduce it in new launchers.
- **`--instance-termination-action=DELETE`**: a preempted backfill VM is deleted (not left STOPPED) so its boot disk
  doesn't accrue cost — the shard re-runs from the manifest on the next wave. (Avoids the orphaned-disk class we cleaned
  up 2026-06-20.)
- **`--no-restart-on-failure`**: don't auto-restart a failed shard on the same VM; the orchestrator / next wave
  re-dispatches incomplete shards (manifest-driven). **If a launcher already passes `--no-restart-on-failure` as its own
  flag, OMIT it from the provisioning string** — gcloud errors on a duplicate flag.

## The launcher contract

Every backfill launcher:

1. Defaults to Spot: `ON_DEMAND=false` (or `ON_DEMAND="${ON_DEMAND:-false}"` when there is no arg-parser).
2. Exposes an escape hatch: `--on-demand` flag **and** `ON_DEMAND=true` env force standard provisioning, for a
   deadline-critical wave that genuinely cannot absorb preemption.
3. Computes the flags and injects them **unquoted** (intentional word-split; gcloud flags carry no spaces) into the
   `gcloud compute instances create` call, with `# shellcheck disable=SC2086` directly above the command:

```bash
# SPOT by default; --on-demand / ON_DEMAND=true forces standard provisioning.
PROVISIONING_FLAGS="--provisioning-model=SPOT --instance-termination-action=DELETE --no-restart-on-failure"
if $ON_DEMAND; then PROVISIONING_FLAGS=""; fi
...
# shellcheck disable=SC2086
gcloud compute instances create "$VM_NAME" \
  --machine-type="$MACHINE_TYPE" \
  ${PROVISIONING_FLAGS} \
  ...
```

For a launcher whose `gcloud` call lives in a shell function or is parsed after the lib is sourced, compute the flags
**at create time** (inside the function, reading the current `$ON_DEMAND`) so a later-parsed `--on-demand` still applies
— see `_tradfi-ohlcv-launcher-lib.sh` (`ohlcv_create_vm`) for the canonical shared-lib shape, and
`launch-mtds-dex-pools-backfill-vm.sh` for the canonical standalone shape.

## What stays ON-DEMAND (the safety line)

**Spot is for backfill only.** These never default to Spot — preemption would lose live data or disrupt a continuous
process:

- **Live / forward-poll / streaming capture** (`launch-mtds-live.sh`, `launch-*-forward-poll.sh`,
  `launch-prediction-live.sh`, `launch-perp-clob-live.sh`, …).
- **Cron / paper-trading / recon / disaster-drill / migration / cutover / dashboard / monitor / watchdog** launchers.
- **Mode-capable launchers** (`launch-features-vm.sh` `--mode {batch|live}`): Spot under `--mode batch`, **forced
  on-demand under `--mode live`** regardless of `ON_DEMAND`.

Classification is by purpose, never by a blanket pattern. When adding a launcher, decide backfill-vs-live first.

**Named exception (operator ruling 2026-07-12, plan-reconciliation finding 357)**: the sports-scheduler runs on SPOT
deliberately (`sports_p0_spot_vm_launchers`, shipped) — its idempotent re-poll makes preemption cheap. This is a single
named carve-out, not a general licence for pollers; any OTHER forward/cron/poll launcher still defaults on-demand per
the classification above unless it earns its own named exception here.

**The inverse case — a one-off migration/verify script whose per-object work is itself expensive is a poor SPOT fit,
even with chunk-checkpointing (2026-07-27 K1/K2 casing-revert migration).** The checkpoint contract above resumes the
`--force`/`redo_all` date FRONTIER cheaply, but a script that content-re-verifies every object it touches (download +
byte-compare, not a cheap manifest-presence check) pays that expensive verification cost again on every object it has to
re-walk after a preemption — the checkpoint tells it where to resume, but resuming is not itself cheap. Wall-clock
progress does not accumulate across repeated preemptions the way it does for a pure backfill's presence-skip. When a
migration/verify launcher's inner-loop cost per unit is dominated by content I/O rather than a manifest check, weigh
`--on-demand` over the default SPOT even though it is a one-off — the 60-91% saving assumes cheap resume, which does not
hold here.

## Manual check-in on a SPOT VM: verify preemption BEFORE diagnosing anything else (HARD RULE, codified 2026-07-23)

The automated `exit_code_fleet_monitor` → `RelaunchPreemptedVm` path below only covers the standard fleet launchers.
**One-off migration VMs (`launch-canonical-migration-vm.sh` and similar) are still SPOT by default but are commonly
watched by a hand-rolled agent/operator watchdog, not the fleet monitor** — for those, checking preemption is on whoever
is doing the check-in, not automatic.

Whenever a SPOT VM you are checking in on looks stalled, gone, or terminal-without-a-normal-exit-marker, run this BEFORE
concluding it's a code bug, a hang, or a monitoring false alarm:

```bash
gcloud compute operations list --project=<project> \
  --filter="targetLink~<vm-name>" \
  --format="table(name,operationType,status,insertTime,statusMessage)"
```

A `compute.instances.preempted` operation, `status=DONE`, is GCP's own record that the instance was genuinely reclaimed
— root cause is confirmed and closed, no further bug-hunting needed; go straight to preemption-recovery (resume from
measured progress, per the HARD RULE below). Its ABSENCE is equally informative: it rules out preemption and means the
disappearance needs real investigation (crash, OOM, manual deletion, or — as found 2026-07-23 — a transient
`gcloud describe` API blip that a watchdog without retry-before-terminal logic misreports as permanent loss; see
`plans/active/defi_consolidated_closeout_2026_07_18.md`'s 2026-07-23 Progress Log entries for both a genuine preemption
and a false-positive caught on the SAME watch run, minutes apart — the two look identical from a single failed
`describe` call and are only distinguishable by checking `operations list`).

## Preemption recovery MUST resume from PROGRESS, never replay START_DATE (HARD RULE, codified 2026-07-18)

Every SPOT VM launched from `deployment-service/scripts/vm/` is preemption-recovered by
`scripts/recovery/relaunch_backfill_vm.py` (`RelaunchPreemptedVm`), triggered by the `PREEMPTED` signal blob and wired
fleet-wide via `scripts/vm/lib/launcher_common.sh`. That relauncher **replays the ORIGINAL launch params — including
`START_DATE`** (its own docstring: _"the SAME venues/START_DATE/concurrency/lease the preempted VM was"_ launched with).

**That is correct ONLY for a skip-enabled backfill**, where presence-skip absorbs the redo and the run resumes
naturally. **It is BROKEN for any `--force` / `redo_all` run**, because force disables the very skip the resume depends
on. Replaying `START_DATE` then restarts the run at day one — forever. The job makes no net progress and burns quota on
every cycle.

Measured 2026-07-18 (sports round-FIXTURES, but the defect is asset-group agnostic): a `--force` backfill over
2019-01-01..2026-07-17 (2,754 days — corrected 2026-08-02, docs-reconcile self-consistency sweep: the range is 2,754
calendar days, not the previously-stated 2,390) ran at ~54 days/hour ⇒ ~51h of runtime, while SPOT preempted it after
~10 minutes of real work. Replay-from-START_DATE would have re-done 2019-01-01..07 on every cycle indefinitely.

**Rules:**

1. A SPOT VM whose run is NOT idempotent-by-skip (i.e. any `--force`/`redo_all` run) MUST resume from **measured
   progress**, not from the original `START_DATE`.
2. Progress is measured the same way a backfill monitor measures it — a count/max of the **target artifact** actually
   created, entity-scoped (see `/codex/12-agent-workflow/async-wait-and-poll-discipline.md`). Never a log or heartbeat.
3. Until the relauncher is progress-aware, a `--force` SPOT run MUST be driven as repeated bounded relaunches from
   `last_completed_unit + 1` (an operator loop or an explicit chunk schedule) — and that requirement belongs in the
   launch plan, not in someone's head.
4. `--on-demand` is NOT the fix. It hides the gap for one job while leaving every other SPOT `--force` run broken, and
   it forfeits the 60-91% cost saving the SPOT default exists for.

**Durable fix — the CHECKPOINT CONTRACT (IMPLEMENTED 2026-07-19).** The VM writes its `last_completed_date` to
`vm-logs/{vm}/PROGRESS.json` as each backfill day-frontier advances, and `RelaunchPreemptedVm` reads it and overrides
`START_DATE` on replay — so a preempted `--force` run RESUMES from its frontier instead of replaying day one. Data-type
agnostic (the VM knows its own units) and **fixes every launcher at once VIA THE SHARED PATH** (no per-launcher edit —
this is the whole point):

- **Writer (two shared seams, both fleet-wide):**
  - UTL `ManifestWriter.record_captured` → `manifest_writer/_vm_progress.py::record_vm_progress` emits a best-effort,
    VM-gated stdout marker `[[VM_PROGRESS]] last_completed_date=<YYYY-MM-DD> monotonic=<bool>` on each day-frontier
    ADVANCE. **ARTIFACT-based** — it fires from a real manifest capture, NEVER a log line, so a `--force` resume can
    never skip a logged-but-unwritten day (the async-poll "count artifacts, not activity" rule). No-op off-VM (`VM_NAME`
    gate).
  - The VM tee-wrapper `deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh` scans appended run.log bytes for the
    latest marker and writes `vm-logs/{vm}/PROGRESS.json` (bounded scan; uploads only on frontier change). It already
    owns that path (run.log + EXIT_STATUS) so the writer needs NO cross-layer bucket resolution.
- **Reader:** `_gcs.read_progress_checkpoint` + the `exit_code_fleet_monitor` PREEMPTED sweep attach the checkpoint to
  the `DP_VM_PREEMPTED` finding; `escalation._recover_preempted_vm` threads it into
  `RelaunchPreemptedVm.relaunch(checkpoint=…)`, which sets `START_DATE=last_completed_date` before replay.
- **SAFETY (monotonic gate):** the override skips `START_DATE` forward ONLY when the frontier is `monotonic` (dates
  recorded in chronological order → everything before the frontier is complete, so resuming from it redoes at most the
  last partial day and skips nothing). A NON-monotonic run (venue-outer iteration) has undone dates behind its max, so a
  `--force` run with a non-monotonic-or-absent checkpoint still PAGEs `force_run_not_replayable` — never a silent gap.
  Non-force runs keep today's verbatim replay when no checkpoint exists. Backward-compatible: no PROGRESS.json ⇒ prior
  behavior.
- **Latent bug also fixed:** `VM_FORCE` was never persisted into `LAUNCH_PARAMS.json`, so the force-PAGE guard was dead
  code that never fired. The guard is now reachable; persisting `VM_FORCE` is part of the per-launcher rollout below.

**Remaining (scope precision, non-blocking) — the per-launcher `lc_write_launch_params` rollout.** Only
`launch-cefi-sharded-backfill.sh` calls it today; the other ~56 SPOT launchers relaunch with the launcher's DEFAULT
venue/scope (broader than the terminated shard, absorbed by idempotent presence-skip) + persist `VM_FORCE`. The DATE
dimension — the day-one-replay bug this section exists for — is fully closed by the checkpoint above regardless of the
rollout. Tracked in `plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md` § G-ops.

**The shared writer seam above is NOT actually universal — it is gated on `ManifestWriter.record_captured` specifically
(`_writer_captured.py::record_captured`, not the sibling `record_captured_from_counts`).** The generic MTDS
`--operation download` orchestrator path (`PartitionedGroupWriter` → `manifest_finalize.py::_write_date_manifest`)
aggregates rows and emits its manifest row via `record_captured_from_counts`, which never calls
`_vm_progress.record_vm_progress` — so every launcher whose Python CLI call routes through that generic download path
was silently getting NO `PROGRESS.json` at all (found by the 2026-07-25 audit; fix shipped `deployment-service@e191d58`,
`infra_satellite_ao_dispatch_batch1_2026_07_26.md` P2). Rather than change the Python aggregation path (higher blast
radius — touches every MTDS download caller), the fix emits the SAME
`[[VM_PROGRESS]] last_completed_date=<date> monotonic=<bool>` marker directly from the shell chunk-loop that already
exists per-launcher-family; the tee-wrapper's grep is agnostic to which layer wrote the marker. Each chunk-loop tracks a
`HAD_FAILURE` flag so a LATER chunk's success can never advance the checkpoint past an EARLIER chunk's failure/kill —
proven via a local bash simulation with a child that self-`kill -9`s mid-run, then a second invocation reading
`PROGRESS.json` back (same methodology as `deployment-service@3d99865`, cefi batch 2).

**`HAD_FAILURE` was itself blind to PARTIAL payload loss within an otherwise-`CHUNK_RC=0` chunk (found + fixed
2026-08-03,** `plans/archive/2026_08/mtds_chunk_had_failure_blind_to_partial_payload_loss_2026_08_03.md`**).** A chunk
where some but not all of that chunk's date-payloads failed (e.g. a transient manifest-consolidator-staleness guard
mid-run) can still exit `0` if at least one payload succeeded — the whole-subprocess `CHUNK_RC` check alone never saw
this, so the checkpoint kept advancing straight through ~28 consecutive lossy chunks in one real incident
(`tradfi-bf-cme-ohlcv-1m-g01-es-es-2020-20260731-134654`, ~a third of 2020 silently under-captured despite
`EXIT_STATUS=0`). Fix (`deployment-service@5478a92`): both `mtds_chunk_loop.sh` and `cefi_coverage_chunk_loop.sh`
generators now also emit each chunk's expected day-count, tee the CLI subprocess's output, and parse its own
`Batch complete: N results collected` line — `N < expected_days` is now treated the same as `CHUNK_RC≠0` for
`HAD_FAILURE`/checkpoint-advancement purposes (`reason=PARTIAL_PAYLOAD_LOSS`, reusing the existing `CHUNK_FAILED:`
greppable prefix). Regression-tested (`TestChunkLoopPartialPayloadLossGating`,
`deployment-service/tests/unit/test_vm_launcher_scripts.py`).

**Per-launcher-family conformance (as of the 2026-08-01 conformance fixes, superseding the original 2026-07-28 P2
fix):**

| Family (VM name prefix)                                                                                         | Mechanism                                                                                                                                                                                                                                                                                                                                                                                              | Status                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `tradfi-bf-*`, `mtds-backfill-tradfi-pipelinecheck`                                                             | `mtds_chunk_loop.sh` (VM_TASK=mtds-backfill, `setup-data-pipeline-vm.sh`)                                                                                                                                                                                                                                                                                                                              | ✅ conformant — shell-level marker added                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `cefi-queue-heavy-binancefutu-x17` (generic Tardis CeFi download, VM_TASK=mtds-backfill)                        | `mtds_chunk_loop.sh`                                                                                                                                                                                                                                                                                                                                                                                   | ✅ conformant — same shared branch                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `cefi-aster`, `cefi-hyperliquid` (VM_TASK=cefi-hl-aster-backfill)                                               | `cefi_hl_aster_loop.sh` (`setup-data-pipeline-vm.sh`)                                                                                                                                                                                                                                                                                                                                                  | ✅ conformant — shell-level marker added                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `canonical-migration-defi-per-instrument`                                                                       | per-year bash chunk loop in `launch-canonical-migration-vm.sh`'s `defi-per-instrument` category                                                                                                                                                                                                                                                                                                        | ✅ conformant — shell-level marker added (full mode only; dry-run never seeds a checkpoint)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `canonical-migration-defi-pi-range`, `canonical-migration-defi-rebuild`                                         | `defi-pi-range`: launch-time bash for-loop precomputing N-day sub-windows (`MIGRATION_PI_RANGE_CHUNK_DAYS`, default 30) in `launch-canonical-migration-vm.sh`, emitting the marker after each window (full-mode only). `defi-rebuild`: `--chunk-days` passed to `rebuild_defi_manifest.py`, which gained a Python-side `_run_chunked()` loop emitting the same marker after each chunk's writer flush. | ✅ conformant — shipped 2026-08-01 (`deployment-service@1e8af34a` + `market-tick-data-service@a2839705`, `infra_satellite_ao_dispatch_batch1_2026_07_26.md`, verified-by-simulation)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `mtds-dex-swaps-backfill` (VM_TASK=defi-backfill), `af-backfill` (VM_TASK=sports-backfill/instruments-backfill) | generic single-shot `elif [ -n "$VM_TASK" ]` fallback in `setup-data-pipeline-vm.sh` now emits ONE end-of-run marker (`last_completed_date=$VM_END_DATE`) on a successful whole-range run, additive-only (no-op for launchers that never set `VM_END_DATE`, e.g. live/websocket tasks); neither launcher fans out so the shared fanout supervisor is untouched                                         | ✅ conformant — shipped 2026-08-01 (`deployment-service@0c5fa5b`, `infra_satellite_ao_dispatch_batch1_2026_07_26.md`, verified-by-simulation; also fixed a related `vm-exec-with-gcs-tee.sh` watchdog race where a marker written just before process exit could be missed — 75s post-marker sleep added)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `instr-backfill-defi-targeted`, `canonical-migration-defi-relabel`                                              | Python `record_captured` (per-instrument/day capture) via `VM_BACKFILL_CMD`                                                                                                                                                                                                                                                                                                                            | ✅ already conformant (pre-existing) — the generic UTL hook fires natively                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `canonical-migration-{cefi,defi,tradfi,prediction}-cdlap` (the `*-candle-apply` categories)                     | `migrate_candle_canonical_2026_07.py`'s own `_CHECKPOINT_BLOB_TPL` (`vm-logs/{vm}/MIGRATION_PROGRESS-shard{shard_index}.json`)                                                                                                                                                                                                                                                                         | ✅ **accepted per-launcher naming exception** (documented 2026-08-01, `infra_satellite_ao_dispatch_batch1_2026_07_26.md`) — a REAL, working checkpoint, just not literally `PROGRESS.json` and not the date/monotonic schema `_gcs.read_progress_checkpoint` parses (it's a 0-based `last_processed_line_index` into one shard's deterministic object enumeration — there's no calendar date to extract). `read_progress_checkpoint` deliberately does NOT special-case it: resume already works WITHOUT that function's help, because `RelaunchPreemptedVm` relaunches the SAME `vm_name` (`VM_NAME_OVERRIDE`, captured in `LAUNCH_PARAMS.json`) and the migration script reads its OWN checkpoint keyed on that `vm_name` internally. The only observable effect is cosmetic — the `DP_VM_PREEMPTED`/`DP_VM_PREEMPTED_RECOVERED` finding never carries a `progress_checkpoint` detail for these VMs even though one exists on disk. See `_gcs.py::read_progress_checkpoint`'s docstring for the full reasoning. |

## A launcher's OWN sequential retry loop MUST back off on a confirmed preemption (codified 2026-08-04)

Distinct from the fleet-wide `RelaunchPreemptedVm` auto-recovery above: several launchers (e.g.
`launch-expected-universe-v2-historical-backfill-vm.sh`'s gated historical chunk backfill) drive their OWN sequential
launch → wait-for-terminal → check-exit-status → relaunch loop in-process, never going through the fleet monitor at all.
**That loop's "confirmed preemption → retry the same window" branch MUST insert a backoff before relaunching — never a
zero-delay `continue` straight back into another launch.** Found + fixed 2026-08-04
(`plans/archive/issues/asia_northeast1_c_spot_preemption_storm_2026_08_04.md` todo 4): a zero-backoff retry loop for the
sports `expected-universe-v2-*` historical backfill (`e2-standard-4`/`asia-northeast1-c`) kept re-entering the SAME
constrained SPOT pool at the instant it had just been reclaimed from, producing 48 VM launches in ~7h, most preempted
within 1-3 min — real billing waste from the launcher's own design, not from SPOT capacity itself. Fix pattern: track
consecutive-preemptions-of-this-chunk, back off with exponential growth capped at a few minutes, reset the streak the
moment a launch actually reaches the workload (not just reaches TERMINATED) — `deployment-service@1861cbe` is the
reference implementation. This is orthogonal to the PROGRESS-checkpoint contract below (that fixes WHAT a relaunch
resumes from; this fixes WHEN a relaunch fires) — a launcher can need both.

## The graceful-flush contract — what "exit gracefully" obliges a process to do (codified 2026-08-13)

The PROGRESS-checkpoint contract above answers _where a relaunch resumes from_. This one answers the question underneath
it: **when a process is told to stop, what must it write out before it dies?** They are different failures. A perfect
checkpoint does not help if the rows the checkpoint refers to were still sitting in a buffer when the process exited.

**The rule.** Any object that can hold un-flushed rows MUST register with the process-wide drain registry
(`unified_trading_library.lifecycle.drain_registry`). Registration is mandatory for every new buffered writer — this is
not opt-in, and a writer that skips it silently loses whatever it is holding on SIGTERM.

```python
from unified_trading_library.lifecycle.drain_registry import (
    DrainPriority, register_drainable, deregister_drainable, install_drain_signal_handler,
)

class MyBufferedWriter:
    def __init__(self, ...):
        install_drain_signal_handler()          # idempotent, main-thread-only, never raises
        register_drainable(self, DrainPriority.DATA_WRITER, name=f"MyBufferedWriter({path})")

    def drain_for_shutdown(self) -> int:
        """Flush what is buffered; return the row count written. Must not raise."""

    def close(self) -> None:
        ...
        deregister_drainable(self)              # in EVERY terminal path, not just the happy one
```

**Register at construction, not at first write.** A writer that dies before its first flush is exactly the case worth
covering.

### Drain ORDER is a correctness property, not a tidiness one

`DrainPriority` is drained low-to-high, and `MANIFEST = 90` is deliberately the highest value in the enum. The manifest
records _what the data writers wrote_. Draining it first would flush rows asserting `captured` for parquet that has not
been uploaded — fabrication-by-construction, the DP-MANIFEST-003 phantom-row class. Anything that computes from written
data drains after the writers and before the manifest (`DERIVED = 50`).

This used to hold only by accident of import sequence, when the manifest and the writers each owned a chained SIGTERM
handler. It is now structural: one handler, one priority-ordered drain.

### Why atexit is not enough, and why the signal handler is not enough either

- **atexit does not run on SIGKILL.** GCE sends SIGTERM on preemption and SIGKILL ~30s later. That is the entire reason
  the signal handler exists. (Measured origin: preempted `mdps-cefi-2019-*` VMs whose run.log showed thousands of real
  aggregations with nothing in the manifest — `DP_VM_GONE_NO_CAPTURE`.)
- **SIGTERM does not unwind a `with` block.** A `StreamingParquetWriter` inside a context manager gets no `__exit__`
  when the process is signalled, so `close()` never runs.
- **Signal installation is last-writer-wins, and a later installer wins silently.** Found 2026-08-13:
  `GracefulShutdownHandler.__init__` (constructed by every `ServiceBootstrap` service in `main()`, i.e. after imports)
  called `signal.signal` unconditionally and REPLACED the drain hook. Its `sys.exit(0)` still ran `manifest_writer`'s
  atexit flush while every `StreamingParquetWriter` buffer — which has no atexit of its own — was discarded. The
  anti-data-loss machinery was manufacturing phantom rows. Fixed at `unified-trading-library@2aacde1359` with two
  layers: the registry registers an atexit backstop at install time (LIFO puts it ahead of `_state`'s flush, preserving
  writers-then-manifest), and `GracefulShutdownHandler` drains explicitly before its cleanup callback.

**Both layers are required.** The atexit backstop covers a clobberer that exits cleanly; only the signal handler covers
a preemption whose SIGKILL is 30 seconds out.

### A drained partial shard is NOT a captured shard

A drain writes bytes. It MUST NOT call `record_captured` and MUST NOT advance the PROGRESS frontier, so the resume
re-attempts that shard. A drain that marked its partial shard complete would be worse than no drain at all: the data is
incomplete AND the manifest claims otherwise, and nothing downstream can tell.

### Async services need one extra line

A service that installs its own handling via `loop.add_signal_handler` bypasses the registry's plain `signal.signal`
hook. Such a service must call `drain_all()` (or at minimum `flush_all_pending_buckets()`) from its own shutdown
sequence.

Contract tests: `unified-trading-library/tests/unit/test_drain_registry.py`.

## Coverage (2026-06-27 fleet-wide conversion)

All GCP backfill launchers in `deployment-service/scripts/vm/` provision Spot by default: ~50 direct-`gcloud` launchers

- the `_tradfi-ohlcv-launcher-lib.sh` shared lib (covers the 7 `launch-tradfi-bf-*` wrappers) + `launch-features-vm.sh`
  (batch-gated). Verify: every `launch-*backfill*.sh` / `launch-tradfi-bf-*.sh` matches `--provisioning-model=SPOT` (the
  runbook verifier). **AWS (`-aws.sh`) backfill launchers are a separate follow-up** — AWS Spot is a different mechanism
  (`--instance-market-options`) and AWS is currently ~100% credit-covered, so converting those extends the credit runway
  rather than cutting cash.

## Related

- [`vm-launcher-runbook.md`](vm-launcher-runbook.md) — the launcher add/change runbook (this standard is part of it).
- [`vm-tarball-deployment.md`](vm-tarball-deployment.md) · [`deployment-observability.md`](deployment-observability.md)
  — VM deployment + no-fire-and-forget observability.
