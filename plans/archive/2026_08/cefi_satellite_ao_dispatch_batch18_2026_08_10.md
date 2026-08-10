---
doc_type: plan
title: CeFi satellite AO batch 18 — MDPS manifest-staleness comparison logic investigation
summary: >-
  Eighteenth AO-dispatch batch for cefi. Extracted from 1 doc found `orphaned_never_touched` + AO-eligible by the
  2026-08-10 `/ag-closeout-audit cefi` run's Phase 1 (`status: open`, never cited by any of the 22 discovered cefi
  covering docs). Single item: investigate the MDPS manifest-consolidated staleness check's comparison logic and runtime
  config value — the reported age (6s) should be far below the threshold (86400s), suggesting the comparison direction
  is inverted or comparing the wrong operands.
status: completed
nature: process
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-18, satellite-docs, mdps, manifest, staleness, ag-closeout-audit]
related:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch18_finalize_2026_08_10.md,
    /plans/archive/2026_08/issues/mdps_manifest_staleness_check_inverted_2026_08_10.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.08
assigned_role: data_engineering
effort: low
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  `/ag-closeout-audit cefi` run 2026-08-10 (ag_closeout_auditor scheduled worker, slot 27, one-shot, `$TRANCHE=cefi`,
  dispatch agt-dab448). Phase 0 pre-filter (`generate_ag_closeout_audit_candidates.py --tranche cefi`) identified 80
  cefi-primary docs, 7 never-cited; per-doc classification confirmed 1 genuinely orphaned cefi-exclusive doc with
  bounded AO-eligible work.
context_scope:
  [
    /plans/archive/2026_08/issues/mdps_manifest_staleness_check_inverted_2026_08_10.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
---

# CeFi satellite AO batch 18 — item-level extraction (2026-08-10 ag-closeout-audit)

> **Status: DRAFT — awaiting operator review before dispatch** (per `/ag-closeout-audit`'s autonomous-mode safety rail;
> flip `status: draft` → `active` only after explicit operator approval).

## Todos

- [x] ✅ [SCRIPT] P3. **Investigate MDPS `Consolidated availability_index ... is stale` comparison logic.** Root cause
      diagnosed: NOT an inverted comparison. Transient GCS/parse error (`OSError`/`ValueError`/`ParserError`) in
      fast-path `_read_consolidated_if_fresh()` (UTL `manifest_writer/_read_index.py:1167`) caused it to return `None`,
      triggering the slow path which raised `ManifestConsolidatorStaleError` with a misleading "older than" message. Fix
      shipped: retry-on-transient when blob is actually fresh (`age < staleness_budget`) + corrected error message from
      "older than" to "staleness threshold". — `unified-trading-library@26294ddf71`. Issue archived at
      `/plans/archive/2026_08/issues/mdps_manifest_staleness_check_inverted_2026_08_10.md` (`status: resolved`).

## Deferred

_None — single-item batch, no conflicts found against the 22 existing covering docs._

## Already covered

_None — this doc was never cited by any of the 22 discovered cefi covering docs
(`generate_ag_closeout_audit_candidates.py --tranche cefi`)._
