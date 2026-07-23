---
doc_type: issue
title: Cross-plan banner sweep findings — 2026-05-11 (extra-hands audit)
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-11
author: ikenna-extra-hands-tab
source:
  [
    plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md § "Cross-plan coordination banners",
    plans/active/work_split_2026_05_11_ikenna.md § "Slot 5",
    plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md (b+ extension),
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-11
---

# Cross-plan banner sweep findings — 2026-05-11

> **Severity**: P2 — informational. **Blast radius**: slot 5 (Ikenna) banner-sweep work item; saves ~30 min of wasted
> cycles by pre-resolving which banners are needed vs not. **Suggested owner**: slot 5 reads + skips the banners flagged
> "NO BANNER NEEDED" below; optionally adds the one OPTIONAL banner if scope allows.

## What I audited

This is an extra-hands read-only audit run from the main workspace clone (NOT slot 5's worktree) to pre-clear the banner
sweep work item in [`work_split_2026_05_11_ikenna.md`](../work_split_2026_05_11_ikenna.md) § "Slot 5". Walked two
banner-target sets:

1. **The 9 plans listed at [code_freeze:328-339](../code_freeze_migrate_backfill_sequencing_2026_05_10.md#L328-L339)** —
   banner pointing at `code_freeze_migrate_backfill_sequencing_2026_05_10.md`.
2. **The 4 plans I called out in the (b+) cascade work** for slot 5 to consider — banner pointing at
   `bucket_name_ssot_canonicalisation_2026_05_10.md` (operator decision (b+)).

## Findings

### Set 1 — code_freeze umbrella banner targets (all 8 unique plans; 9 line items in code_freeze list two banners on aws_migration_defi_first which is a single file)

All 8 ✅ banners present + correctly tagged:

| Plan                                                                                                      | Banner line | Tag      | Status |
| --------------------------------------------------------------------------------------------------------- | ----------- | -------- | ------ |
| [`master_to_live_defi_2026_05_23.md`](../master_to_live_defi_2026_05_23.md)                               | line 26     | BE-AWARE | ✅     |
| [`gcs_migration_bundle_pipeline_mode_2026_05_08.md`](../gcs_migration_bundle_pipeline_mode_2026_05_08.md) | line 547    | BE-AWARE | ✅     |
| [`aws_migration_defi_first_2026_05_07.md`](../aws_migration_defi_first_2026_05_07.md)                     | line 19     | BE-AWARE | ✅     |
| [`writegate_honest_coverage_endtoend_2026_05_06.md`](../writegate_honest_coverage_endtoend_2026_05_06.md) | line 32     | BLOCK    | ✅     |
| [`features_repo_consolidation_2026_05_08.md`](../features_repo_consolidation_2026_05_08.md)               | line 931    | BLOCK    | ✅     |
| [`live_pipeline_mtds_mdps_features_2026_05_08.md`](../live_pipeline_mtds_mdps_features_2026_05_08.md)     | line 938    | BE-AWARE | ✅     |
| [`manifest_evolution_master_2026_05_08.md`](../../epics/manifest_evolution_master_2026_05_08.md)          | line 29     | BLOCK    | ✅     |
| [`manifest_migration_master_2026_05_07.md`](../../epics/manifest_migration_master_2026_05_07.md)          | line 27     | BLOCK    | ✅     |

**Slot 5 action**: NONE. All banners present + correctly tagged. The "Cross-plan coordination banner sweep (helper to
slot 1 P0 banner verification)" P1 todo in slot 5 work-split § Scope is **already satisfied for the 9 code_freeze banner
targets** as of PM@1b9e6451 yesterday.

### Set 2 — (b+) cascading plans I flagged for slot 5 banner consideration

| Plan                                                                                                                          | Bucket-name reference content                                                          | Verdict          | Action                                                                                                                                                                                                                                                                                                                                                                                                                             |
| ----------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`simulation_scenarios_topology_price_shocks_2026_05_09.md`](../simulation_scenarios_topology_price_shocks_2026_05_09.md):380 | "Reuses UTL emission helpers — no new bucket-naming logic; uses bucket_naming.py SSOT" | NO BANNER NEEDED | Pure consumer of the SSOT; doesn't change bucket shape. The (b+) decision doesn't change consumer-side behavior (it changes which bucket names resolve to). Banner would be noise.                                                                                                                                                                                                                                                 |
| [`client_reporting_pnl_attribution_mvp_2026_05_10.md`](../client_reporting_pnl_attribution_mvp_2026_05_10.md):135             | "bucket_naming.py SSOT"                                                                | NO BANNER NEEDED | Pure consumer of the SSOT. Same reasoning.                                                                                                                                                                                                                                                                                                                                                                                         |
| [`_AUDIT_2026_05_07_dependency_graph.md`](../_AUDIT_2026_05_07_dependency_graph.md):102, 116, 128                             | Audit-doc references to bucket-name discipline                                         | NO BANNER NEEDED | Audit doc, not a plan with todos. Already references the discipline correctly. The (b+) decision doesn't invalidate the audit's findings (which were about discipline, not specific bucket names).                                                                                                                                                                                                                                 |
| [`deployment_ui_lifecycle_tabs_2026_05_08.md`](../deployment_ui_lifecycle_tabs_2026_05_08.md):29, 392                         | "env-tier topology for deployment-UI/API itself"                                       | OPTIONAL banner  | This plan implements the deployment-UI env-tier hosting (per `/codex/05-infrastructure/deployment-ui-architecture.md` § "Environment tier"). Under (b+) Phase 0g this is verified-already-shipped infrastructure. A banner here would point readers at the (b+) operator decision so they know the bucket-side context exists. **Recommendation**: skip unless slot 5 has time; the codex doc already cross-references everything. |

**Net slot 5 action under this audit**: skip all 4 banner additions. The work-split § Slot 5 P1 banner sweep item
(extended in PM@2d6b131c with these 4 plans) can be marked done with reference to this findings doc, OR optionally add
ONE banner on `deployment_ui_lifecycle_tabs_2026_05_08.md` for cross-reference courtesy.

## Composes with

- [`work_split_2026_05_11_ikenna.md`](../work_split_2026_05_11_ikenna.md) § "Slot 5" — pre-clears the banner-sweep P1
  work item.
- [`bucket_name_ssot_canonicalisation_2026_05_10.md`](../bucket_name_ssot_canonicalisation_2026_05_10.md) — operator
  decision (b+) extension.
- [`code_freeze_migrate_backfill_sequencing_2026_05_10.md`](../code_freeze_migrate_backfill_sequencing_2026_05_10.md) §
  "Cross-plan coordination banners" — confirms 8/8 already present + correct.
- CLAUDE.md "Cross-Plan Coordination Banners" HARD RULE — this audit follows the rule's reader-contract pattern.
- CLAUDE.md "Findings Triage Discipline" — case 4 (outside every active plan) → issue doc; this is the issue doc.
