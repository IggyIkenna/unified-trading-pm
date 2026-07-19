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
    vm-launcher-runbook.md,
    vm-tarball-deployment.md,
    deployment-observability.md,
    aws-migration-cost-snapshot-2026-05-07.md,
  ]
created: 2026-06-27
authoritative_for: [Spot-VM provisioning standard for backfill launchers]
referenced_by:
  [
    codex/05-infrastructure/vm-launcher-runbook.md,
    codex/05-infrastructure/vm-tarball-deployment.md,
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
2019-01-01..2026-07-17 (2,390 days) ran at ~54 days/hour ⇒ ~44h of runtime, while SPOT preempted it after ~10 minutes of
real work. Replay-from-START_DATE would have re-done 2019-01-01..07 on every cycle indefinitely.

**Rules:**

1. A SPOT VM whose run is NOT idempotent-by-skip (i.e. any `--force`/`redo_all` run) MUST resume from **measured
   progress**, not from the original `START_DATE`.
2. Progress is measured the same way a backfill monitor measures it — a count/max of the **target artifact** actually
   created, entity-scoped (see `codex/12-agent-workflow/async-wait-and-poll-discipline.md`). Never a log or heartbeat.
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
