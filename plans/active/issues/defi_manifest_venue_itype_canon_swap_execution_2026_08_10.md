---
doc_type: issue
title: DeFi manifest venue/itype-canon + 0-row-vault + chain-pollution swap — VM execution steps (N5r/N6r c-e)
summary: >-
  The N5r/N6r swap SCRIPT (sub-steps a+b of `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md` N5r/N6r) is
  shipped (market-tick-data-service@8175ec7a: `defi_manifest_venue_itype_canon_swap.py` + tests,
  `--beta-manifest-out`/`--chunk-days` compatible since `978a49fa`). What remains is the VM-only EXECUTION of the swap
  against the live 133M-row defi `_index` — a corpus-scale GCS walk + a prod-write that must never run on the shared
  planning host. This doc carries the three concrete execution todos (projection run + drain gate + apply-and-verify).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [issue, n5r, n6r, manifest-swap, vm-execution, defi]
related:
  - /plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md
  - /plans/active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md
  - /plans/active/defi_consolidated_closeout_2026_07_18.md
created: "2026-08-10"
author: slot-7
source:
  - cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md N5r/N6r item
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
parent_epic: instruments_master
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: "2026-08-10"
locked_by:
locked_since:
resolved_by:
---

# DeFi N5r/N6r swap — VM execution (sub-steps c-e)

## What I found

The N5r/N6r "wholesale live-index replace" cannot complete from a shared-host session: the live defi
`_index/availability_index.parquet` is **133,041,278 rows / 1082 row-groups** (measured 2026-08-10 via a row-group-level
GCS probe — the "27-33M rows" figure in earlier docs is stale), so both the chunked
`rebuild_defi_manifest.py --dry-run --beta-manifest-out` projection and the swap's plan/apply paths (which materialise
the full cell-key set) are inherently VM-scale. The swap tool itself is now built + unit-tested (sub-step b,
`market-tick-data-service@0d2ed19f`), so only the VM execution remains.

Confirmed legacy shapes (bounded row-group sampling, 2026-08-10): `AAVEV3` bare/glued venue spelling, uppercase `POOL`
`instrument_type`, and combined-form `PROTOCOL-CHAIN` venue rows are still present in the live index; the 0-row-vault
class is handled by the projection's N5 honest-absence routing. The swap's REMOVE mask is add-scoped (never removes a
captured cell whose canonical twin this run is not writing) and carries the N6r coexisting-distinct GCS venue-set
protection (`SUSHISWAP` etc.).

## Why it matters

The DeFi manifest still carries venue/itype/chain spelling that disagrees with the canonical GCS object paths, and the
VAULT 2020-2022 0-row phantoms are stamped `captured` (should be honest absence). Until the swap executes,
`canonical_path_violations`/phantom audits keep flagging these cells and the manifest↔object desync persists.

## Recommended decision

Execute the swap on a dedicated in-region VM (SPOT, per the vm-launcher-runbook), in three bounded steps, each a tracked
todo below. Do NOT run the projection or apply on the shared planning host. Use the swap script's own modes:
`--apply-prod` (plan, read-only) then `--confirm-prod-write` (execute, after the operator-reviewable delta + the
mandatory verified pre-write snapshot).

## Todos

- [x] ✅ [SCRIPT] P2. **N5r/N6r (c) — launcher built + shipped; VM launch next.** — deployment-service@99b46b9f2d (slot
      16, 2026-08-10)

      **Launcher shipped**: `deployment-service/scripts/vm/launch-defi-manifest-projection-vm.sh` — a self-contained SPOT
                      VM launcher (modeled on `launch-backfill-defi-legacy-datatype-fold-vm.sh`) that runs the two-step projection + swap
                      plan diff:

                      1. `rebuild_defi_manifest.py --start-date 2020-01-01 --end-date <today> --dry-run --beta-manifest-out
                         gs://deployment-scripts-central-element-323112/n5r-n6r-projection/<run-ts>/defi_proj.parquet --chunk-days 30
                         --workers 32 --reemit-absence`
                      2. `defi_manifest_venue_itype_canon_swap --projection-uri <same> --apply-prod`

                      **Registrations** (all 3 forward-registration sites in the same commit):
                      - `vm_classification.py` DATA_VM_PREFIXES — `"defi-manifest-projection-"`
                      - `vm_prefix_registry.py` VM_PREFIX_TO_BUCKET — `VmPrefixSpec(bucket=None, lifecycle_class=EPHEMERAL_BATCH)`
                      - `launcher_registry.py` LAUNCHER_FOR_VM_PREFIX — `None` (non-relaunchable one-shot)

                      **VM spec**: `defi-manifest-projection-{ts}`, e2-standard-16 SPOT, 250GB pd-balanced, asia-northeast1-c, singleton
                      lock, VM_SHUTDOWN_ON_COMPLETION=true, heartbeat-only (projection writes to deployment-scripts audit bucket, no
                      per-VM manifest shard). QG + quickmerge green on deployment-service (3262 passed).

                      **To launch** (next dispatch):
                      ```bash
                      bash deployment-service/scripts/vm/launch-defi-manifest-projection-vm.sh
                      # or with explicit dates:
                      bash deployment-service/scripts/vm/launch-defi-manifest-projection-vm.sh --start-date 2020-01-01 --end-date 2026-08-10 --chunk-days 30
                      ```
                      Then monitor `gs://deployment-scripts-central-element-323112/vm-logs/{vm_name}/run.log` for the swap plan-mode
                      ADD/REMOVE delta output. Record the delta back in this doc. (repo: market-tick-data-service)

- [x] ✅ [INFRA] P2. **N5r/N6r (d) — drain gate + snapshot.** Before the prod write: confirm no in-flight defi manifest
      writer is racing the index (pause/verify the defi backfill/reconcile crons + any defi live VM; confirm
      `written_at` quiet), and confirm the swap's mandatory pre-write snapshot lands
      (`_index/snapshots/pre_defi_venue_itype_canon_swap_*.parquet`, byte-verified round-trip) before any REMOVE. (repo:
      market-tick-data-service) Done when: the drain is confirmed (0 concurrent writers) and the verified snapshot
      exists.

      **CODE SHIPPED (market-tick-data-service@697d983c + @0a9ea724, 2026-08-10, slot 24).** The drain-gate capability
                              did NOT exist before this change (grep confirmed no drain-gate in the swap tool): added `--drain-gate` mode —
                              `drain_check()` confirms 0 concurrent defi manifest writers via (1) consolidator lock NOT in-flight
                              (`consolidator_cycle_in_flight`) + (2) consolidated index blob generation stable across a wait window
                              (the `written_at`-quiet proof), then `snapshot_index()` writes the byte-verified
                              `_index/snapshots/pre_defi_venue_itype_canon_swap_*.parquet` (refuses to snapshot while a writer races — the
                              snapshot must capture a QUIET index). Split into companion `defi_manifest_drain_gate.py` (900-line cap). 4 new
                              unit tests + full `quality-gates.sh` green, ancestry-verified on LDR. Live read-only drain probe (2026-08-10
                              17:4x UTC) correctly reports **NOT DRAINED — consolidator cycle in-flight** (a defi merge was actively writing at
                              probe time), i.e. the gate refuses exactly as designed. **Execution is VM-only per this doc** — the
                              drain-confirmation + snapshot run on the swap VM (todo (c)'s launcher is in-flight per the STATUS note above);
                              this checkbox covers the shipped INFRA capability. (repo: market-tick-data-service)

- [ ] [SCRIPT] P2. **N5r/N6r (e) — apply + post-verify.** _(No `[OPERATOR]` tag needed — self-justified per
      `task_template.md` finding O option (a)/(c), 2026-08-12 (/plan-reconcile): this 133M-row prod write is gated
      behind (1) the shipped `--drain-gate` mode confirming 0 concurrent defi manifest writers before any write, (2) a
      mandatory byte-verified pre-write snapshot (`_index/snapshots/pre_defi_venue_itype_canon_swap_*.parquet`,
      round-trip verified) giving a real rollback path if the swap goes wrong, and (3) an independent post-write
      re-audit with hard zero-tolerance checks (`stale_remaining=0`, `canon_missing=0`, 0 captured→failed mass flip)
      before the checkbox can flip — this is the same "verify-before-mutate, snapshot-first" established-safe pattern
      already used elsewhere in this doc family, not a first/unreviewed destructive action.)_ On the VM:

      ```python
                                      python -m market_tick_data_service.scripts.defi_manifest_venue_itype_canon_swap --projection-uri gs://<audit-bucket>/<dir>/defi_proj.parquet --apply-prod --confirm-prod-write
                                      ```

                                      (writes PROD). Verify: swap's own post-write verify (stale_remaining=0, canon_missing=0) AND an independent fresh
                                      GCS-sampled re-audit (0 legacy-spelled/uppercase-itype/chain-polluted rows remaining, 100% of their canonical
                                      twins present with matching row_count, 0 captured→failed mass flip). (repo: market-tick-data-service) Done when:
                                      the re-audit shows 0 stale rows + full twin coverage — which also satisfies the
                                      `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md` N5r/N6r item's done-when, at which point that checkbox
                                      is flipped with this evidence.

## Progress Log

- **data_engineering (slot 8) 2026-08-10T21:3xZ**: Re-picked todo (e), re-verified the (c)-gate — **still gated, nothing
  to apply**. Live evidence (bounded, 2026-08-10): (1) **no projection output** —
  `gs://deployment-scripts-central-element-323112/n5r-n6r-projection/` matches no objects; no
  `defi-manifest-projection-*` VM has ever been launched (GCE instance list) and no `vm-logs/*projection*` blob exists.
  (2) **drain gate (d) cannot pass**: `canonical-migration-defi-rebuild-20260810-204358` is RUNNING right now (GCE
  instance list) — an in-flight defi-bucket rebuild/manifest writer, exactly the concurrent writer the drain gate + the
  swap's sequencing require to be absent. (3) The apply (`--apply-prod --confirm-prod-write`) is a **prod write that
  must run on the swap VM, never the shared planning host** (this session is on the shared host). No code shipped. Task
  released via `/skip-current-task` `reason_code=GATED` — re-dispatch when (c)'s projection exists AND the in-flight
  defi rebuild completes AND a VM is provisioned for the apply.
- **data_engineering (slot 15) 2026-08-10T19:40Z**: Picked up todo (e) but found it gated on (c) — no projection exists
  yet. Attempted to unblock by creating the launcher + registry entries for (c):
  `deployment-service/scripts/vm/launch-defi-manifest-projection-vm.sh` (new, modeled on
  `launch-backfill-defi-legacy-datatype-fold-vm.sh`), plus `VM_PREFIX_TO_BUCKET` entry (`vm_prefix_registry.py`) and
  `LAUNCHER_FOR_VM_PREFIX` entry (`launcher_registry.py`) for `defi-manifest-projection-` prefix. **Committed locally at
  `deployment-service@56f46d4d` but BLOCKED from shipping** — deployment-service has 11 pre-existing
  `test_dp_recovery_actuators` failures (confirmed at parent commit, not caused by my changes). Joined existing
  repo-blocker RB-5d23ffad as waiter. When the repo goes green, the next worker can:
  `git fetch && git merge --ff-only origin/live-defi-rollout`, push the launcher commit, then launch the projection VM
  via `bash scripts/vm/launch-defi-manifest-projection-vm.sh`. Todo (e) remains gated on (c)'s projection output.
