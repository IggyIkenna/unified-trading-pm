---
doc_type: issue
title: ag-closeout-audit ui parked findings — 2026-08-07
summary: >-
  Parked findings from the scheduled ag_closeout_auditor run (2026-08-07, tranche=ui, slot 9, dispatch agt-eb521b).
  Phase 0-2 complete: candidate set unchanged from 2026-08-06 (12 tranche-primary docs), orphan count unchanged at 9 of
  12 (composition shifted — 2 docs moved never-touched to partial-coverage now that batch1 exists and cites them). 3
  findings: 2 plausible `ui` mistag candidates (informational, not retagged — folded into the tranche's already-tracked
  corpus-wide retag todo) and 1 Phase-1 result summary (incl. a stale-todo correction applied directly to
  `ui_satellite_ao_dispatch_batch1_2026_08_06.md`, still draft/unshipped). No batch2 drafted — nothing conflict-clear
  emerged; recommend approving + dispatching batch1 instead.
status: open
nature: issue
asset_group: [ui]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ag-closeout-audit, parked, ui, orphan, mistag]
related:
  [
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
    /plans/active/ui_satellite_ao_dispatch_batch1_2026_08_06.md,
    /plans/active/issues/deployment_api_prod_disable_auth_true_2026_08_06.md,
    /plans/active/issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md,
    /plans/active/issues/ag_closeout_audit_defi_parked_2026_08_07.md,
  ]
created: 2026-08-07
parent_epic: deployment_and_user_management_master
assigned_vm: NA
priority: P3
last_updated: 2026-08-07
source: >-
  ag_closeout_auditor scheduled run 2026-08-07 (tranche=ui, slot 9, DISPATCH_ID=agt-eb521b)
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
    /plans/active/ui_satellite_ao_dispatch_batch1_2026_08_06.md,
  ]
---

# ag-closeout-audit ui parked findings — 2026-08-07

## Finding 1 (informational) — plausible `ui` mistag, currently `[cross-cutting]`: live P1 prod security issue

`plans/active/issues/deployment_api_prod_disable_auth_true_2026_08_06.md` (created 2026-08-06, one day old) carries
`asset_group: [cross-cutting]`, `parent_epic: infrastructure_master`,
`repos: [deployment-api, unified-trading-library]`.

**Content read in full**: `DISABLE_AUTH=true` is live on prod `uts-shared-deployment-api` Cloud Run service because the
startup guard reads `UnifiedCloudConfig.environment` but the service only sets `DEPLOYMENT_ENV` — every route under
`_authenticated_router` (`/api/deployments/*`, `/api/services/*`, `/api/builds/*`) is currently reachable with ZERO
authentication. `unified-trading-library` is touched only incidentally (that's where the config field is defined, not a
fix target) — every named fix candidate, context_scope path, and the actual bug surface is 100% `deployment_api/*`. This
matches the exact "bare cross-cutting tag on single-AG content" mistag pattern this skill's SKILL.md documents (the
`understat_bulk_download_backfill` / `defi_migration_audit_log` precedents) — `ui`'s declared scope explicitly names
"auth flow" as in-tranche.

**Not retagged in this run** — deliberately conservative for two reasons: (1) this doc is CURRENTLY tagged
`cross-cutting`, meaning a concurrent `cross-cutting`-tranche sibling worker may be reading/auditing this exact file
right now (the skill's own "running as one of N concurrent sharded tranche workers" hard rule reserves writes to a
shared doc for its owning tranche, and ownership here isn't 100% unambiguous — `unified-trading-library` is a genuinely
shared/cross-cutting-owned config surface even though the bug instance is deployment-api-specific); (2) the `ui`
tranche's own corpus-wide retag audit is already a named, deliberately-scoped-separately todo
(`ui_consolidated_closeout_2026_07_30.md`'s P2 todo #5) rather than something to do piecemeal mid-daily-audit.

**Recommendation**: Fold into the next corpus-wide `ui` retag pass (the already-tracked P2 todo #5) alongside its 2
existing named candidates (`monitoring_control_plane_master_2026_06_10.md`, `ui_build_warm_cache_2026_06_17.md`). Not
itself AO-eligible regardless of tag (its own 4 todos are explicitly judgment/audit-gated: "decide fix shape (a) vs
(b)", "audit every current caller" — no bounded worker-determinable outcome yet).

## Finding 2 (informational) — plausible `ui` mistag, currently `[defi]`, corroborated by a sibling tranche run same day

`plans/active/issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md` carries `asset_group: [defi]`,
`repos: [deployment-ui, unified-api-contracts]`. Independently flagged the SAME day by the `defi`-tranche
`ag_closeout_auditor` run (slot 7, dispatch agt-6f12db) — see `issues/ag_closeout_audit_defi_parked_2026_08_07.md`
Finding 2: "stale deployment-ui bundled capability data... tag should be `[ui]`... likely auto-tagged `defi` because
DRIFT/Pacifica are Solana DeFi venues [but] neither is actually scoped to the defi asset_group." Not independently
re-verified by full content read in THIS run (time-boxed — see Progress Log) — flagging the cross-tranche corroboration
so it isn't lost, not asserting a fresh independent finding. The defi audit also names a second doc in the same finding
(`architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md`, repos
`[unified-api-contracts, unified-trading-system-ui]`) as `[ui]`-or-`[cross-cutting]`-candidate — also un-verified here.

**Recommendation**: Same as Finding 1 — fold both into the next corpus-wide `ui` retag pass rather than retag
unilaterally mid-audit (both currently tagged into a DIFFERENT tranche's ownership; per the multi-tranche primary-owner
rule, a retag write belongs to whichever tranche's content-scope actually wins, decided by a real per-doc read, not by
whichever auditor got there first).

## Finding 3 — Phase 1 result: orphan composition shifted as expected, no new conflict-clear items, batch2 not drafted

Phase 1 (12-agent Workflow, one per tranche-primary doc) completed after Findings 1-2 were written. Full verdict tally
(12 docs total):

- `archivable_now`: 1 — `deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md` (unchanged from 2026-08-06;
  still fully done but stuck at a stale `status: open` + an impossible `locked_since` predating `created` — still not
  this skill's to fix, flagging again for `/plan-reconcile ui` or `/archive-candidates-audit`). **Superseded pointer
  (2026-08-10 formalization sweep)**: this same finding, still unresolved as of the 4th consecutive audit pass, is now
  formalized as a real `- [ ]` todo in the more current `ag_closeout_audit_ui_parked_2026_08_09.md`'s `## Todos`
  section — not re-formalized here to avoid a duplicate.
- `archivable_after_planned_work`: 2 — `deployment_registry_firestore_migration_2026_07_14.md` (self-covered by its own
  P3/P5 phase-chain), `deployment_api_sigabrt_crash_loop_2026_07_24.md` (self-dispatched, `assigned_vm: planning`, still
  an extremely active 900+-line live investigation — both unchanged from 2026-08-06).
- `orphaned_partial_coverage`: 2 — `data_status_cell_grid_rearchitecture_2026_07_18.md` and
  `artifact_pipeline_observability_2026_07_17.md`. **Both MOVED here from `orphaned_never_touched`** since 2026-08-06 —
  expected, not a new problem: `ui_satellite_ao_dispatch_batch1_2026_08_06.md` didn't exist at 2026-08-06's Phase-0
  discovery time (it was Phase 3's OUTPUT that day), so today's Phase 0 correctly discovered it as part of the covering
  set, and its 3 real Todos cite specific items in exactly these 2 docs. Both still have substantial uncovered remainder
  (6/7 and 10/12 items respectively) — see the batch1 Progress Log entry dated 2026-08-07 for the full break down.
- `orphaned_never_touched`: 7 — `consolidator_throughput_backlog_monitor_2026_07_09.md`,
  `data_status_catalogue_true_source_phase2_2026_07_24.md`, `data_status_tab_and_downloads_remediation_2026_06_16.md`,
  `deployment_registry_firestore_p3_cutover_2026_07_14.md`, `deployment_registry_firestore_p5_verify_2026_07_14.md`,
  `issues/cost_observability_deferred_followups_2026_07_10.md`,
  `issues/deployment_api_inventory_alert_gate_ondemand_only_2026_07_27.md` — all unchanged from 2026-08-06; all 7 are
  named only in batch1's `## Deferred` section (analysis, not coverage) under operator-gated / time-gated /
  too-large-or-risky / needs-verification categories, none of which cleared since yesterday (verified via
  `git log --since="2026-08-06 12:00"` on every one of the 12 candidate files, cross-checked against each Phase-1
  agent's own independent read — zero material changes found anywhere).
- `exclude_cross_cutting`: 0 — Orthogonality HARD CHECK clean, consistent with 2026-08-06.

**Net orphan count: 9 of 12 (unchanged from 2026-08-06's 9 of 12; composition shifted 2 docs from never-touched to
partial-coverage as described, not a regression).**

**Bonus finding, folded into `ui_satellite_ao_dispatch_batch1_2026_08_06.md` directly rather than repeated here**: the
`artifact_pipeline_observability_2026_07_17.md` Phase-1 agent found batch1's own Todo 2 ("file a new
artifact-pipeline-metadata-gaps issue doc") was based on a stale read — the source doc's own text already states this
filing was done 2026-07-21 under a different name, and the "verify bug #2" instruction refers to a bug already resolved
as not-a-bug. Corrected directly in batch1 (still draft, unshipped — safe to fix pre-approval) rather than noted here as
a separate todo, since it's a same-document, same-run correction. See batch1's 2026-08-07 Progress Log entry for the
full before/after.

**No batch2 drafted this run.** Per the skill's iterative-drain guidance ("stop iterating once every remaining orphaned
doc's open work is purely from the non-batchable taxonomy... report the residual count... rather than continuing to spin
batches that can't possibly extract anything new"): batch1 found zero conflict-gated items originally (nothing existed
yet to conflict with, being the tranche's first batch), and re-checking all 11 Deferred items today found zero
newly-cleared (no operator ruling landed, no time-gate passed, in the 1 day since). Drafting a competing batch2 against
the same 12 docs before batch1 even ships would be redundant. The correct next step is operator approval + dispatch of
batch1, followed by its finalize plan's own todo 2 (re-check all 11 Deferred items), which is the tranche's designed
mechanism for surfacing batch2 candidates — not another `/ag-closeout-audit` pass in the meantime.

## Progress Log

- **2026-08-07 (ag_closeout_auditor, dispatch agt-eb521b, slot 9)**: Phase 0 discovery complete — candidate set
  confirmed unchanged from 2026-08-06 (12 docs via `generate_ag_closeout_audit_candidates.py --tranche ui`), covering
  set is `ui_consolidated_closeout_2026_07_30.md` + `ui_satellite_ao_dispatch_batch1_2026_08_06.md` (still
  `status: draft`, unapproved) + its finalize. Findings 1-2 surfaced during Phase 0's discovery pass (checking for
  new/changed docs since the prior run). Phase 1 (12-agent Workflow) completed cleanly (12/12, 0 errors) — see Finding 3
  for the full result. Parked-count reconciliation: 3 findings, all 3 written to this doc. ✓ No batch2 drafted (see
  Finding 3's rationale). Full per-doc classification evidence: Workflow run `wf_435a1f38-064`, journal at
  `subagents/workflows/wf_435a1f38-064/journal.jsonl` (session-local, not corpus-durable — this doc + batch1's own
  Progress Log are the durable record).
- **na-eligibility-audit 2026-08-07 (ui tranche)**: KEEP-NA, valid — a point-in-time ag-closeout-audit findings record,
  not a dispatchable work item; all 3 findings are already actioned (2 folded into the tracked corpus-wide `ui` retag
  todo, 1 is this same day's result summary) and content is current as of today.
- **context-scout 2026-08-09**: populated context_scope (3 entries).
- **2026-08-10 (prose-findings formalization sweep)**: converted 0 prose findings into 0 formal todos (0 already
  resolved). Findings 1-2 (mistag candidates) are already tracked by `ui_consolidated_closeout_2026_07_30.md`'s P2
  todo #5 (confirmed via grep). The `archivable_now` stuck-lock item is genuinely actionable but superseded by the more
  current `ag_closeout_audit_ui_parked_2026_08_09.md`, which now carries the formal todo — added a superseded-pointer
  note above rather than duplicating it here.
