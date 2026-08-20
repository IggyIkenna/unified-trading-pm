---
doc_type: plan
title: Manifest v9 residual — orphaned epic-body checkboxes extracted from manifest_master
summary: >-
  6 live `[AGENT]`/`[OPERATOR]` checkboxes lived directly in the `plans/epics/manifest_master.md` epic body, invisible
  to every plan-corpus tool (all scan `plans/active/*.md`, never `plans/epics/*.md`). Extracted verbatim into this LOCAL
  tracking doc per operator ruling on `plan_reconciler_findings_cross_cutting_2026_08_10.md` Item F — epics are meant to
  be derived rosters, not carry live checkboxes.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [market-tick-data-service, unified-trading-library, unified-api-contracts, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [manifest, bucket, canonicalisation, hygiene, epic-extraction]
related:
  [
    /plans/epics/manifest_master.md,
    /plans/archive/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md,
    /codex/05-infrastructure/bucket-isolation-model.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-15"
last_updated: 2026-08-17
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
effort: low
drift_direction: advance-code
supersedes:
superseded_by:
source: "Extracted from plans/epics/manifest_master.md per operator ruling, /plan-reconcile session 2026-08-15"
depends_on: []
context_scope:
  [
    /plans/epics/manifest_master.md,
    /plans/archive/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md,
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    market-tick-data-service/market_tick_data_service/scripts/,
    market-tick-data-service/market_tick_data_service/cli/handlers/_defi_manifest.py,
  ]
locked_by:
locked_since:
---

# Manifest v9 residual — orphaned epic-body checkboxes

## Why this doc exists

`plans/epics/manifest_master.md` (the manifest L1 epic) carried 6 live `- [ ]` `[AGENT]`/`[OPERATOR]` checkboxes
directly in its own body (under "## Deferred work — migrated from archived plans" and its two `> **MIGRATED FROM:**`
sub-sections), a leftover from earlier plan-archival migrations that folded their still-open remainder straight into the
epic text instead of a real tracked plan. Every corpus-wide plan/todo tool (`regen_backlog_from_plan.py`,
`count_open_tasks.py`, the hygiene sweep) scans `plans/active/*.md` only — `plans/epics/*.md` is never ingested — so
these 6 items were a genuine orphan class: real, still-open work, permanently invisible to tooling.

Found + routed by `plan_reconciler` (cross-cutting tranche, 2026-08-10) as Item F, deferred as a structural/judgment
call ("how should live epic-body checkboxes be made visible to plan-corpus tooling?"). Operator-approved resolution
(2026-08-15): **extract** — move the 6 items verbatim into a real `plans/active/` doc (this one), leave a pointer in the
epic. This doc is `assigned_vm: NA` (LOCAL/human track, the default per `task_template.md` — not authorized to set
`planning` without a separate operator ask); it is not dispatched by AO, but its todos ARE now visible to every
corpus-wide plan-hygiene tool, closing the orphan gap Item F identified.

Text below is moved verbatim from `plans/epics/manifest_master.md` (was lines 224, 265, 268, 274, 277, 280 as of
2026-08-15) — priorities/tags preserved from the source exactly, not re-derived.

## Todos

> Migrated from `bucket_name_ssot_canonicalisation_2026_05_10.md` (archived 2026-05-23) — bucket naming SSOT complete
> for DeFi/CeFi/core paths; remaining items are env-tiered migration + prediction bucket + workspace audit.

- [ ] [AGENT] P2. **[2026-07-12 correction]** `ManifestWriter.add` is a LIVE, actively-extended write path, NOT
      dead/soft-deprecated code awaiting a grep-confirm-then-delete (was: "Design and land a successor plan for full
      `ManifestWriter.add` deletion: that method was soft-deprecated in the wave-2 plan (Phase 3 swapped all call sites
      to `record_captured`/`record_empty`)... grep workspace for any remaining `.add(` call sites → confirm 0 remaining
      callers → delete `ManifestWriter.add`" — false premise). Re-verified 2026-07-12: 4 live non-test call sites in
      market-tick-data-service — `market_tick_data_service/scripts/_rebuild_sports_write.py:187`,
      `market_tick_data_service/scripts/_rebuild_cefi_cf11.py:184`,
      `market_tick_data_service/cli/handlers/_defi_manifest.py:474`,
      `market_tick_data_service/scripts/rebuild_defi_manifest.py:478` — and this exact last call site was actively
      enhanced as recently as M-COORD-5 (mtds@f80c50f1, per
      `/plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md`: writer.add(...) now passes
      asset_group=defi + the source-aware pipeline_mode/source/transport). **MIGRATED FROM:
      plans/archive/wave2_polymarket_record_captured_from_counts_2026_05_09.md Phase 4.** Corrected todo: any future
      deletion of `ManifestWriter.add` must first migrate these 4 live call sites to `record_captured`/`record_empty` —
      do not merely grep-confirm zero callers, there are non-zero callers today. Corrected per plan-reconciliation
      finding 137, `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 "50 reclassified"
      blanket ruling. Done-when: all 4 call sites migrated to `record_captured`/`record_empty` and a fresh
      workspace-wide grep of `.add(` against `ManifestWriter` shows 0 remaining callers.

> Migrated from `bucket_name_ssot_canonicalisation_2026_05_10.md` (archived 2026-05-23) — bucket naming SSOT complete
> for DeFi/CeFi/core paths; remaining items are env-tiered migration + prediction bucket + workspace audit.

- [x] ✅ [AGENT] P2. Extracted to `cross_cutting_satellite_ao_dispatch_batch14_2026_08_17.md` item 11 (na-eligibility-audit 2026-08-17). **Workspace-grep audit for legacy bucket references** — run workspace-wide grep to verify zero inline
      `gs://` f-strings remain after bucket SSOT rollout. Generate audit table confirming all call sites use
      `resolve_bucket_name()`. Update QG ratchet baseline. Done-when: the audit table is produced and the QG ratchet
      baseline for inline `gs://` usage reflects 0 remaining violations (or is lowered to match a genuinely-zero count).
- [ ] [AGENT] P2. **Legacy bucket rename delegation** — delegate any remaining legacy bucket renames to the appropriate
      service-repo owners. Confirm each service's QG STEP 5.69 check is green. Done-when: every named service-repo owner
      has confirmed (or the delegating todo cites) QG STEP 5.69 green.

> Migrated from `manifest_schema_final_gate_2026_05_09.md` (archived 2026-05-23) — v8 schema design complete; Phases
> 8-13 are execution gates tracked in mtds_mdps_master + master plan.

- [ ] [OPERATOR] P1. **Phase 0.A+0.B pre-audit** — run `gcs_migration Phase 0` pre-audit on same-region test bucket +
      `measure-honest-coverage.py` on production manifests for each asset_group before full migration execution. Human
      sign-off required before Phase 9 VM launches. Done-when: pre-audit report produced + operator sign-off recorded.
- [ ] [AGENT] P2. **Phase 4.DEFAULT-REMOVAL-v8kwargs** — remove `= None` defaults from v8 schema kwargs across UTL
      `ManifestWriter` + UAC schema definitions; enforce required fields. Low urgency once v8 migration runs are
      complete. Done-when: `= None` defaults removed from the named v8 schema kwargs and required-field enforcement is
      live, `quality-gates.sh` green.
- [ ] [OPERATOR] P1. **Phase 8.A+8.B sign-off** — operator reviews class-C triage rows + appends sign-off section to
      `manifest_divergence_triage_2026_05_09.md` confirming production manifest state post-migration. Done-when: the
      sign-off section is appended to that doc with the operator's explicit confirmation.

## Progress Log

- **2026-08-15 (extraction)**: created this doc, moved the 6 items above verbatim out of
  `plans/epics/manifest_master.md` (per operator ruling on `plan_reconciler_findings_cross_cutting_2026_08_10.md` Item
  F), left a pointer in the epic. No content changed beyond adding an explicit done-when line to each (none had one) and
  correcting one bare `active/master_data_canonicalisation_migration_catalogue_2026_06_07.md` cross-reference to the
  leading-slash repo-root-relative convention.
- **na-eligibility-audit 2026-08-17** [body-hash:d5da20f6b18619f3]: RECLASSIFY (per-todo split) -- extracted the 1 bounded item (workspace-grep audit for legacy gs:// bucket references) to cross_cutting_satellite_ao_dispatch_batch14_2026_08_17.md item 11. Doc stays assigned_vm: NA for its remaining items. Cross-cutting tranche audit.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries) — added the live `ManifestWriter.add` call-site paths named in Todo 1 (the scripts/ dir covering 3 of 4 live call sites, plus the most recently-enhanced 4th).
