---
scope: [engineer, admin]
title: Spot VMs for Backfill — the provisioning standard
type: infrastructure
status: living
last_reviewed: 2026-06-27
execution:
  owner: "deployment-platform"
  cadence: "per VM-launcher add/change"
  verifier:
    "rg -L 'provisioning-model=SPOT' deployment-service/scripts/vm/launch-*backfill*.sh (every backfill launcher must
    match)"
  last_executed: "2026-06-27 (fleet-wide conversion)"
---

# Spot VMs for Backfill — the provisioning standard

> **HARD RULE.** Every **backfill / idempotent** VM launcher provisions GCP **Spot** VMs by default
> (`--provisioning-model=SPOT`). Spot is ~60–91% cheaper than on-demand. Backfill is idempotent (per-shard manifest
> resume via `VM_NAME` + `MANIFEST_PER_VM_SHARDS=true`), so a preempted shard re-runs cleanly — there is no correctness
> cost to preemption, only a restart. **On-demand for backfill is now a bug**, not a default.

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
