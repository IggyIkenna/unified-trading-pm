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
