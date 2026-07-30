---
doc_type: issue
title: reconcile_phantom_manifest_rows_all.py's full-manifest read for defi now exceeds 64GB (OOM/stall on e2-highmem-8)
summary:
  Running reconcile_phantom_manifest_rows_all.py against the defi manifest (via
  merge_canonical_with_outstanding_shards's full-column, full-row materialization) OOM-killed a 16GB VM instantly and
  stalled a 64GB VM at 96% memory without completing. A scoped, 6-column pyarrow read of the same 27.3M-row file
  completed in well under a minute. Proposes a lighter-weight read path for verification/audit use cases that don't need
  the full frame, mirroring the cf_manifest_audit.py precedent already used for this same corpus.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service, unified-trading-library, deployment-service]
scope: [engineer]
tags: [manifest, memory, oom, infra-capacity, defi, reconciliation]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/issues/pyth_oracle_prices_stale_ghost_failure_rows_2026_07_28.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: 2026-07-28
source: ["mvp_backfill_defi_onchain_v10-002 / pyth_oracle_prices_stale_ghost_failure_rows_2026_07_28.md, 2026-07-28"]
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
parent_epic: infrastructure_master
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
assigned_role: infra
---

## What I found

Attempting to run `reconcile_phantom_manifest_rows_all.py --asset-group defi --report-pyth-oracle-prices-ghost-failures`
(or any pass through this script for defi — the memory cost is incurred by the shared `main()` read path before any
flag-specific logic runs) hit genuine memory-capacity limits twice in the same session, 2026-07-28:

1. **On the shared slot host** (61GB total, shared with other concurrent slot workloads): RSS grew to ~34GB and host
   swap filled (15/15Gi used) after 13 minutes with the process still in `merge_canonical_with_outstanding_shards`'s
   initial read — never printed past `Loading manifest from ...`. Killed manually (exact PID) to protect the shared host
   before it could OOM other slots' work.
2. **On a dedicated `e2-standard-4` VM (16GB, the manifest-recon launchers' existing default)**: the VM's own kernel
   OOM-killed the process at **15.4GB RSS**, 228 seconds after the `--dry-run` step (the first of the 3-4 chained
   scripts) started — before any subsequent step (including a newly-added PYTH-ghost step) ever ran.
3. **On a dedicated `e2-highmem-8` VM (64GB)**: did NOT OOM-kill, but stalled. The VM's own `deployment_heartbeat.py`
   metrics (`host_metrics_window` in its deployment-registry JSON) show `mem_pct` climbing near-linearly (27.9% → 96.0%)
   between 06:16:33Z and 06:24:35Z, then BOTH the heartbeat daemon and the live `run.log` GCS uploader went silent for
   18+ minutes while the VM stayed `RUNNING` — consistent with severe swap-thrashing rather than a clean OOM-kill (no
   `Out of memory: Killed process` kernel line ever appeared in the serial console). SSH attempts to inspect it live
   also hung (though raw TCP:22 stayed responsive, ruling out a full network freeze). Deleted the VM rather than wait
   indefinitely.

**Ruled out**: an inflated `merge_canonical_with_outstanding_shards` cost from many outstanding per-VM shard files —
only 9 objects existed under `_index/per_vm/` for defi at the time (this normally explains an inflated merge cost per
the script's own staleness-guard docstring, but wasn't the case here).

**Confirmed the underlying corpus itself doesn't require this much memory for a SCOPED read**: a direct pyarrow read of
the SAME `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` (27,278,596 rows),
restricted to 6 columns (`date/venue/data_type/capture_status/instrument_id/error_reason`) instead of the full wide
schema (v4→v9 columns including `pipeline_mode`/`service_emission_state`/
`last_emission_decision_at`/`expected_window_completeness_fraction`/etc.), completed in well under a minute with no
memory pressure, verified two ways (parquet-level predicate pushdown, and a full-row/6-column read with post-hoc pandas
filtering).

## Why it matters

- `reconcile_phantom_manifest_rows_all.py --asset-group defi` (any flag) is currently **not reliably runnable** even on
  a dedicated `e2-highmem-8` (64GB) VM — a real regression risk for the NEXT person who needs to run a defi
  phantom/ghost-row/absence-reason audit or apply pass, not just this session's specific flag.
- The precedent already exists that this corpus needs deliberate provisioning: `cf_manifest_audit.py`'s Cloud Run job
  (`deployment-service/terraform/gcp/cf_manifest_audit_scheduler.tf`) is provisioned at **32Gi/8vCPU** specifically
  because "4Gi and even 16Gi/4vCPU OOM'd on the largest bucket (defi tick, 26.3M rows)" per that file's own comments.
  This reconciler's read path is evidently heavier than `cf_manifest_audit.py`'s (which succeeds at 32Gi on the same
  corpus) — `merge_canonical_with_outstanding_shards` materializes the FULL wide schema, while a scoped/column-pruned
  read of the same file is cheap, suggesting the wide-schema full materialization (not raw row count) is the multiplier.
- Every future defi phantom-row / absence-reason / legacy-blank / PYTH-ghost reconciliation pass (dry-run OR apply)
  inherits this same risk until addressed.

## Recommended decision — needs a design call, not a mechanical fix

Two non-exclusive directions:

1. **Provision manifest-recon VMs for defi at cf_manifest_audit.py's proven 32Gi+/8vCPU-equivalent size (or larger,
   given even 64GB stalled here) by default**, not just via the ad-hoc `MACHINE_TYPE` override this session added
   (`deployment-service@420c8be`) — e.g., bump the defi-specific default machine type, or move defi manifest-recon
   passes to a Cloud Run job mirroring `cf_manifest_audit_scheduler.tf`'s own provisioning, per the manifest
   consolidator's own Cloud-Run-not-VM precedent.
2. **Add a lighter-weight, column-pruned read path** to `merge_canonical_with_outstanding_shards` (or a scoped sibling
   helper) for callers that only need a handful of columns / a single (venue, data_type) slice — mirroring the pattern
   this session used ad hoc for verification. This would let dry-run/verification-only callers avoid the full
   materialization entirely, reserving the expensive full-frame path for callers that genuinely need to WRITE back the
   whole index (the actual `--apply` mutation path, which needs full-frame safety guarantees regardless).

Given this session's actual task resolved via other means (see
`/plans/archive/issues/pyth_oracle_prices_stale_ghost_failure_rows_2026_07_28.md`'s Progress Log, now
resolved/archived), this doc is filed to prevent the same wall from blocking the next defi manifest-recon need, not
because it is currently blocking anything urgent.

- [ ] [INFRA] P2. **Retagged from [OPERATOR] 2026-07-28 — direction 1 adopted by default, no operator decision needed.**
      `cf_manifest_audit.py`'s Cloud Run job (`deployment-service/terraform/gcp/cf_manifest_audit_scheduler.tf`) is the
      existing, proven precedent for this exact corpus (32Gi/8vCPU, explicitly provisioned because 4Gi/16Gi OOM'd on the
      same ~26.3M-row defi tick manifest) — adopt that sizing/pattern as the default for defi manifest-recon rather than
      the ad-hoc per-run `MACHINE_TYPE` override this session used (`deployment-service@420c8be`): either bump the
      defi-specific default VM machine type to a 32Gi+/8vCPU-equivalent size, or move defi manifest-recon passes to a
      Cloud Run job mirroring `cf_manifest_audit_scheduler.tf`'s own provisioning (matching the manifest consolidator's
      own established Cloud-Run-not-VM precedent). (repo: deployment-service)
- [ ] [SCRIPT] P3. **Follow-on efficiency improvement (direction 2), not gating on the above.** Add a lighter-weight,
      column-pruned read path to `merge_canonical_with_outstanding_shards` (or a scoped sibling helper) for callers that
      only need a handful of columns / a single (venue, data_type) slice — mirroring the ad-hoc 6-column pyarrow read
      this session used for verification (completed in well under a minute with no memory pressure on the same 27.3M-row
      file). Reserve the expensive full-frame path for callers that genuinely need to WRITE back the whole index (the
      real `--apply` mutation path, which needs full-frame safety guarantees regardless). (repo: instruments-service,
      unified-trading-library)

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY -> assigned_vm: planning (conflict-check CLEAR against 231 active
  planning docs; no open todo elsewhere duplicates this claim) - both todos retagged from [OPERATOR] with direction 1
  adopted; bounded machine-type/Cloud-Run sizing + a column-pruned read path
