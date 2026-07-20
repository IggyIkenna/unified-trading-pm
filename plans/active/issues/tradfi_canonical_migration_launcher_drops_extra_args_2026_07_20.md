---
doc_type: issue
title:
  "launch-canonical-migration-vm.sh tradfi branch silently DROPS MIGRATION_EXTRA_ARGS — gated flags never reach the
  migrate pass"
summary:
  The `tradfi` category branch of `launch-canonical-migration-vm.sh` builds its compound 3-pass command and then, unlike
  every other category, never appends `MIGRATION_EXTRA_ARGS`. Any flag passed that way is silently discarded — including
  the destructive `--purge-massive` / `--massive-backfill-verified` gate. A run intending an authorized massive purge
  would purge NOTHING while `full` mode simultaneously ran an `--apply` content migration (copy→verify→delete-source)
  over the whole non-massive tradfi estate. Caught in pre-flight audit; nothing was executed.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [deployment-service, market-tick-data-service]
scope: [engineer, admin]
tags: [canonical-migration, vm-launcher, destructive-gate, massive-purge, data-correctness, silent-failure]
related:
  [
    massive_purge_blocked_databento_l1_entitlement_2026_07_20,
    tradfi_consolidated_closeout_2026_07_18,
    tradfi_canonical_path_migration_design_2026_07_19,
    codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: 2026-07-20
priority: P0
parent_epic: tradfi_master
source: "Pre-flight audit of the authorized Massive purge (slot-1, 2026-07-20)"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm:
resolved_by:
---

# `tradfi` launcher branch silently drops `MIGRATION_EXTRA_ARGS`

## The defect

`deployment-service/scripts/vm/launch-canonical-migration-vm.sh` appends `MIGRATION_EXTRA_ARGS` in exactly two places —
line 302 (`tradfi-catalogue-canon`) and line 320 (the generic `else`, explicitly excluding `defi-per-instrument`). The
`tradfi` branch does not:

```bash
if [[ "$cat" == "tradfi" ]]; then
    cmd="$(_tradfi_content_migration_cmd "$vm_name")"   # <-- no MIGRATION_EXTRA_ARGS append
elif [[ "$cat" == "tradfi-catalogue-canon" ]]; then
    cmd="$(_catalogue_canon_cmd)"
    [[ -n "${MIGRATION_EXTRA_ARGS:-}" ]] && cmd="$cmd ${MIGRATION_EXTRA_ARGS}"
```

So `MIGRATION_EXTRA_ARGS=... bash launch-canonical-migration-vm.sh tradfi <start> <end> full` discards the flags with no
warning and no non-zero exit. The launcher's own header (lines 21-24) documents `MIGRATION_EXTRA_ARGS` as the way to
pass `--stamp`, which makes the silent drop actively misleading.

## Why this is P0 rather than cosmetic

It converts an intended narrow destructive action into a broad one:

- **The authorized action does not happen.** `--purge-massive` / `--massive-backfill-verified` never reach
  `migrate_tradfi_canonical_2026_07`, so every massive object classifies `PURGE_REFUSED_GATED` — **0 purged**.
- **A much larger unintended one does.** `full` mode is `--apply` on all three passes (`--quarantine` on passes 2/3).
  The migrate pass's `A_COPY` disposition is copy→verify→**delete source**, so every non-canonical NON-massive object in
  `raw_tick_data/**` gets moved. That is the whole `batch_databento` estate — precisely what a zero-collateral check is
  supposed to prove untouched.

Sampled scale of the non-massive estate that `full` would move: 187-612 `batch_databento` objects per day across 2,040
`day=` prefixes.

## Second, independent blocker on the same path

The gate resolves the sentinel with `Path(args.massive_backfill_verified).is_file()` — evaluated **on the VM**. A
sentinel written locally (repo or laptop) does not satisfy it. Any purge run must stage the sentinel onto the VM and
pass its on-VM path.

## Fix options (not applied — a destructive execution path should not be redesigned unreviewed)

- **A (recommended)** — give the purge its own narrow path rather than widening `full`: run `migrate_...` alone (no
  rebundle/recover, no `--quarantine`) against an enumeration **pre-filtered to `pipeline_mode=batch_massive`**, with
  the sentinel staged on the VM. Zero collateral becomes structural — non-massive objects are not in the input — and it
  needs no change to the migrate tool. Confirmed feasible: on every sampled day `massive + databento == total_parquet`
  exactly, so the filter is exact.
- **B** — plumb `MIGRATION_EXTRA_ARGS` into the `tradfi` branch. Necessary for flag delivery but **not sufficient**:
  `full` mode still runs the other two `--apply` passes, so the estate-wide migration still happens alongside the purge.
- **C** — make the drop loud: fail fast if `MIGRATION_EXTRA_ARGS` is set for a category that ignores it. Cheap, and
  prevents the whole class of silent-discard bug. Worth doing regardless of A/B.

## Follow-up todos

- [ ] [INFRA] P0. Fix the silent discard — implement **C** (loud failure for ignored `MIGRATION_EXTRA_ARGS`) in
      `launch-canonical-migration-vm.sh`. (repo: deployment-service)
- [ ] [INFRA] P0. Implement **A** — a purge-only invocation over a `batch_massive`-filtered enumeration with the
      sentinel staged on the VM, before any authorized purge runs. (repo: deployment-service)
- [ ] [OPERATOR] P0. Confirm intent: the authorized action is a massive-only purge. Was the estate-wide canonical
      content migration (`full` mode, non-massive copy→delete-source) also intended in the same run, or must it be a
      separate reviewed operation?
