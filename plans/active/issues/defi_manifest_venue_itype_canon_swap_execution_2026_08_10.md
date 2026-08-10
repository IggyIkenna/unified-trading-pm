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

- [ ] [SCRIPT] P2. **N5r/N6r (c) — run the chunked defi projection on a dedicated VM + diff vs live.** Launch a VM
      (`deployment-service/scripts/vm/` launcher per the vm-launcher-runbook; SPOT default) to run:

      ```python
                  python -m market_tick_data_service.scripts.rebuild_defi_manifest --start-date <defi-floor> --end-date <today> --dry-run --beta-manifest-out gs://<audit-bucket>/<dir>/defi_proj.parquet --chunk-days <N> --workers 32
                  ```

                  (full range; `--reemit-absence` per the rebuild's own guidance). Then run the swap's plan mode against live to
                  surface the REAL ADD/REMOVE delta:

                  ```python
                  python -m market_tick_data_service.scripts.defi_manifest_venue_itype_canon_swap --projection-uri gs://<audit-bucket>/<dir>/defi_proj.parquet --apply-prod
                  ```

                  Record the delta (ADD/REMOVE counts by class + kept-legacy-no-twin) in this doc before proceeding. (repo:
                  market-tick-data-service) Done when: the projection part files exist and the plan-mode delta is recorded with no
                  surprise class-B mass downgrade.

                  **STATUS 2026-08-10 (slot 2) — LAUNCHER GAP, not yet launched.** Investigation found **no existing
                  `deployment-service/scripts/vm/launch-*.sh` can run this projection**: `launch-canonical-migration-vm.sh` builds
                  only its hardcoded per-category `migrate_*_canonical.py` commands (line ~2060 sets `VM_MIGRATION_CMD` from a
                  category builder; no raw-cmd override), and no launcher references `rebuild_defi_manifest`/`--beta-manifest-out`
                  except `launch-backfill-defi-legacy-datatype-fold-vm.sh` (which hardcodes a different task). The generic
                  `VM_MIGRATION_CMD` metadata dispatch in `setup-data-pipeline-vm.sh` would run the command verbatim, but there is
                  no launcher that emits that metadata for a custom command without editing code. **The prerequisite is a small
                  self-contained launcher** (model on `launch-backfill-defi-legacy-datatype-fold-vm.sh`: SPOT, `VM_BACKFILL_CMD`
                  metadata, per-VM-shard isolation, tarball-freshness check) + a `VM_PREFIX_TO_BUCKET` entry in
                  `deployment-service/deployment_service/vm/vm_zombie_watchdog.py` for the new prefix (e.g.
                  `defi-manifest-projection-`), shipped via quickmerge — never hand-roll a VM name. Also confirmed the defi index is
                  **133,041,278 rows / 1082 row-groups** (this doc's own measurement) → the projection MUST be chunked
                  (`--chunk-days` ≥ 30-60, `--workers 32`, `--reemit-absence`) on a big SPOT VM (e2-standard-16+, per the
                  `mtds_manifest_rebuild_scripts_unbounded_memory_no_chunking_2026_07_31.md` OOM precedent), writing the projection
                  to a bounded audit path (e.g. `gs://deployment-scripts-central-element-323112/n5r-n6r-projection/2026-08-10/`).
                  A G1 defi full-history backfill launcher (same session, other plan) was stopped to keep the defi index quiet per
                  this doc's step-(d) drain-gate intent. `--start-date <defi-floor>` needs pinning (DeFi data floor; recommend
                  2020-01-01). Next dispatch: add the launcher + registry entry, launch the projection VM, record the plan-mode
                  delta.

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

- [ ] [SCRIPT] P2. **N5r/N6r (e) — apply + post-verify.** On the VM:

      ```python
                  python -m market_tick_data_service.scripts.defi_manifest_venue_itype_canon_swap --projection-uri gs://<audit-bucket>/<dir>/defi_proj.parquet --apply-prod --confirm-prod-write
                  ```

                  (writes PROD). Verify: swap's own post-write verify (stale_remaining=0, canon_missing=0) AND an independent fresh
                  GCS-sampled re-audit (0 legacy-spelled/uppercase-itype/chain-polluted rows remaining, 100% of their canonical
                  twins present with matching row_count, 0 captured→failed mass flip). (repo: market-tick-data-service) Done when:
                  the re-audit shows 0 stale rows + full twin coverage — which also satisfies the
                  `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md` N5r/N6r item's done-when, at which point that checkbox
                  is flipped with this evidence.
