---
doc_type: codex-ssot
title: Cross-Asset Rescan Protocol
summary:
  Operational SSOT for the cross-asset manifest rescan (instruments-service/scripts/cross_asset_rescan.py) — walks the
  canonical manifest per asset_group, detects 5 drift classes, auto-fixes class-A flips (--apply / VM_APPLY_FLIPS) and
  routes class-C ambiguous rows to a triage JSONL; per-VM shard isolation + singleton-lock + RESCAN_* events.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, instruments-service]
scope: [engineer, admin]
tags: [manifest, migration, cross-asset, spot-vm, data-correctness, single-walk]
related:
  [
    ../../plans/archive/2026_05/manifest_cross_asset_rescan_design_2026_05_08.md,
    /codex/02-data/chunk-safe-manifest-migrations.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-05-19
authoritative_for: [cross-asset manifest rescan drift-detection protocol]
referenced_by: [/codex/02-data/chunk-safe-manifest-migrations.md]
owner:
last_reviewed: 2026-05-19
code_refs:
---

# Cross-Asset Rescan Protocol

> **STATUS** — Shipped 2026-05-12 as Phase 3 of
> [`manifest_schema_final_gate_2026_05_09`](../../plans/active/manifest_schema_final_gate_2026_05_09.md). Design SSOT:
> [`plans/active/manifest_cross_asset_rescan_design_2026_05_08.md`](../../plans/active/manifest_cross_asset_rescan_design_2026_05_08.md).

## Purpose

The cross-asset rescan walks the canonical manifest across all asset groups, detects 5 classes of drift (path-prefix,
instrument-type casing, schema-4 empty rows, chain-bundle equivalence, hive-vocab), and either auto-fixes class-A drift
or routes class-C ambiguous rows to a triage JSONL for operator review.

## Key files

| Component           | Path                                                                        | Commit    |
| ------------------- | --------------------------------------------------------------------------- | --------- |
| Orchestrator script | `instruments-service/scripts/cross_asset_rescan.py` (333 lines)             | `a264f21` |
| VM launcher         | `deployment-service/scripts/vm/launch-cross-asset-rescan-vm.sh` (184 lines) | `19fad8c` |
| Deploy-api slug     | `deployment_api/services/deploy_missing.py` `_SERVICE_LAUNCHER_SCRIPTS`     | `c8a1cd4` |
| Watchdog prefix     | `deployment-service/scripts/vm/vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` | `19fad8c` |

## Rescan flip schema (two drift classes)

| Class | Description                                  | Action                                                        |
| ----- | -------------------------------------------- | ------------------------------------------------------------- |
| A     | Unambiguous flip — disk reality is canonical | Auto-fixed when `VM_APPLY_FLIPS=true`; written as flip record |
| C     | Ambiguous — both sides have plausible claim  | Written to triage JSONL; operator decides per row             |

## Runtime contract

**Dry-run by default.** Pass `--apply` to the launcher (or `VM_APPLY_FLIPS=true` env) to enable class-A writes.

```bash
# Dry-run (no writes)
bash deployment-service/scripts/vm/launch-cross-asset-rescan-vm.sh --asset-group cefi

# Apply class-A auto-fixes
bash deployment-service/scripts/vm/launch-cross-asset-rescan-vm.sh --asset-group cefi --apply
```

`asset_group` accepts: `cefi | defi | tradfi | sports | prediction | cross_asset_all`

## Per-VM shard isolation

- `VM_NAME` env injected by launcher → scoped to a unique per-run shard tag
- `MANIFEST_PER_VM_SHARDS=true` enforced; rescan writes use the per-VM shard path
- Watchdog prefix `cross-asset-rescan-` is registered (heartbeat-only; rescan writes to canonical manifest)

## Singleton-lock

Launcher holds a GCS singleton lock for the asset-group. Concurrent launches on the same asset-group are rejected —
check for a running VM before re-launching.

## Events emitted

All events land at `gs://{project_id}-events/events/instruments-service/...` keyed on `run_id`.

| Event                    | When                                    |
| ------------------------ | --------------------------------------- |
| `RESCAN_RUN_STARTED`     | Orchestrator boots                      |
| `RESCAN_SHARD_STARTED`   | Per asset-group shard starts            |
| `RESCAN_SHARD_COMPLETED` | Shard finished successfully             |
| `RESCAN_SHARD_FAILED`    | Shard errored (isolated; run continues) |
| `RESCAN_RUN_STOPPED`     | Orchestrator exits cleanly              |
| `RESCAN_RUN_FAILED`      | Orchestrator exits with unhandled error |

## Triage JSONL output

Class-C rows written to `gs://{project_id}-rescan-triage/{run_id}/triage.jsonl`.

Operator review workflow (Phase 8 of the manifest final gate plan):

1. Download triage JSONL: `gcloud storage cp gs://{pid}-rescan-triage/{run_id}/triage.jsonl .`
2. For each row, decide: (a) flip per disk, (b) flip per manifest, (c) leave as-is
3. Record decision in `manifest_cross_asset_rescan_design_2026_05_08.md` § "Rescan triage decisions"

## Pre-flight checklist before running

1. `vm_zombie_watchdog.py` is running with the current `VM_PREFIX_TO_BUCKET` dict (restart after any dict edit)
2. Tarballs refreshed: `bash deployment-service/scripts/vm/create-code-tarballs.sh --all`
3. No concurrent rescan VM running for the target asset-group

## Related

- Design doc: `plans/active/manifest_cross_asset_rescan_design_2026_05_08.md`
- Manifest schema plan: `plans/active/manifest_schema_final_gate_2026_05_09.md` § Phase 3
