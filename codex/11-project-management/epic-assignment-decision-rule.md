---
doc_type: codex-ssot
title: Epic assignment decision rule — asset-group vs shared-mechanism vs cross-cutting
summary: >-
  The test for which of the 22 current epics a plan/issue's `parent_epic:` should declare, and why the 5
  asset-group epics (cefi/defi/tradfi/sports/predictions_master) were kept as their own epics during the
  2026-08-18/19 epic-taxonomy restructure rather than dissolved into pipeline-stage epics. Authoritative for the
  HARD RULE cited from CLAUDE.md's "Plans — format + authoring discipline" section.
status: current
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [epic-taxonomy, parent-epic, plan-authoring, codex-ssot]
authoritative_for: [epic-assignment, parent-epic-selection]
related:
  [
    /plans/epics/README.md,
    /codex/11-project-management/epic-taxonomy-2026-08-18.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
    /codex/11-project-management/plan-priority-tier-and-dispatch-ordering.md,
  ]
referenced_by:
owner:
last_reviewed: 2026-08-19
code_refs:
created: "2026-08-19"
author: claude
last_updated: "2026-08-19"
---

# Epic assignment decision rule

## The test

**Would this exact fix look meaningfully different, or not exist at all, if you swapped the asset group?**

- **Yes** — the content is asset-group-SPECIFIC (a particular adapter, a venue quirk, an asset-group-specific
  archetype) → the asset-group epic: `cefi_master`, `defi_master`, `tradfi_master`, `sports_master`,
  `predictions_master`.
- **No** — the fix lives in shared code/infra that serves every asset group identically → the epic that owns that
  shared mechanism: `instruments_master` (instrument reference data), `mtds_mdps_master` (market-tick-data reader/
  writer plumbing, candles), `features_and_ml_master` (features DAG + ML inference/training), `manifest_master`
  (manifest v9 discipline), `uac_master` (schema/registry/contract-governance), `strategy_master` (strategy-service,
  PnL/HWM), `execution_master` (execution-service handlers).
- **Workspace-wide, not owned by any single service or asset group** → the cross-cutting epics: `ci_master`,
  `security_and_cross_cutting_master`, `observability_master`, `batch_live_symmetry_master`,
  `client_isolation_and_governance_master`, `system_readiness_master`, `deployment_and_user_management_master`,
  `plan_hygiene_master`, `orchestrator_master`, `agent_operating_framework_master`.

## The edge case that trips people up

A finding SURFACED via one asset group is not automatically that asset group's epic. If a cefi backfill run exposes
a bug in the shared MTDS reader, the fix's `parent_epic` is `mtds_mdps_master` — not `cefi_master` — because the
same bug would have hit defi/tradfi/sports/predictions equally; the asset group was just where it happened to be
noticed first. Ask "is the FIX asset-group-specific" (test above), never "where was this FOUND."

The reverse also holds: a fix that touches `mtds_mdps_master`'s reader code but only because of a `cefi`-specific
data shape (e.g., a CEFI-only symbol format edge case in the reader's cefi branch) stays asset-group-specific if the
change genuinely doesn't affect the other asset groups' code paths — apply the test to the CODE CHANGE, not the
file it lives in.

## Why the 5 asset-group epics were kept, not dissolved (2026-08-19 ruling)

During the 2026-08-18/19 epic-taxonomy restructure, folding the 5 asset-group epics into pipeline-stage epics was
considered and rejected. Unlike the epics that WERE folded (`dart_and_promote_master`,
`escalation_and_disaster_recovery_master`, `infrastructure_master`, `trading_agent_master`,
`global_ledger_pnl_attribution_master` — all had 0 active corpus references at fold time), the 5 asset-group epics
each carry a substantial, active, cross-pipeline-stage body of work: `tradfi_master` 46 active docs, `sports_master`
68, `cefi_master` ~50, `defi_master` ~49, `predictions_master` ~20 (measured 2026-08-19, `epic_report_data.py`).
Folding them would mean:

1. **Re-triaging ~230 active docs** across 5-10 pipeline-stage/cross-cutting epics, one at a time, per the test
   above — the exact audit this doc exists to make repeatable, not a one-time mechanical move.
2. **Losing the asset-group-level view entirely** — "everything blocking cefi going live" stops being answerable
   as a single epic query the moment cefi's docs scatter across `mtds_mdps_master`/`execution_master`/
   `strategy_master`/etc. by pipeline stage.

The asset-group epics stay as the SSOT for asset-group-specific adapters, venue quirks, and archetypes; shared
mechanism work still routes to its owning pipeline-stage epic per the test above, even when it was found via one
asset group.

## Consolidation folds that DID happen (for contrast)

Fold candidates are docs/epics with **near-zero active corpus references at decision time** — the actual criterion
used, not epic size or "thinness" alone. Two live epics were checked and found genuinely thin as of 2026-08-19
(`execution_master`: 1 active doc; `client_isolation_and_governance_master`: 3) but were NOT folded, because a low
open-doc count can mean "quiet right now" (most work already shipped) rather than "dead" — the same shape as
`dart_and_promote_master` before its own fold was confirmed against 0 references, not assumed from its name. Before
folding any epic, run `rg -c "^parent_epic: <slug>$" plans/active/*.md plans/active/issues/*.md` and check the
epic's own `related_plans:` frontmatter — a real fold candidate has ~0 in both, not just a low number in one.

## Auditing existing assignments

To check whether an already-tagged doc's `parent_epic` matches this rule, ask the test above against the doc's own
`summary:` and its actual diff/content — not its filename or its `asset_group:` frontmatter field (which tracks a
different axis: WHICH asset group the content concerns, independent of which EPIC owns the tracking). A doc can
legitimately carry `asset_group: [cefi]` while its `parent_epic` is `mtds_mdps_master`, if the fix is shared-reader
code that happened to be found via cefi.
