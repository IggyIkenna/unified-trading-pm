---
doc_type: issue
title: ag-closeout-audit ui parked findings — 2026-08-07
summary: >-
  Parked findings from the scheduled ag_closeout_auditor run (2026-08-07, tranche=ui, slot 9, dispatch agt-eb521b).
  Phase 0 discovery confirmed the candidate set is unchanged from the 2026-08-06 baseline (12 tranche-primary docs, 3
  covering docs — closeout + batch1 [status: draft, unapproved] + finalize), and surfaced 2 plausible `ui` mistag
  candidates (1 found directly, 1 corroborated from a sibling defi-tranche run the same day). Phase 1 (12-agent Workflow
  classification) was in flight at the time this doc was first written — see Progress Log for whether additional
  findings were appended after it completed.
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

## Progress Log

- **2026-08-07 (ag_closeout_auditor, dispatch agt-eb521b, slot 9)**: Phase 0 discovery complete — candidate set
  confirmed unchanged from 2026-08-06 (12 docs via `generate_ag_closeout_audit_candidates.py --tranche ui`), covering
  set is `ui_consolidated_closeout_2026_07_30.md` + `ui_satellite_ao_dispatch_batch1_2026_08_06.md` (still
  `status: draft`, unapproved) + its finalize. Findings 1-2 above surfaced during Phase 0's discovery pass (checking for
  new/changed docs since the prior run). Phase 1 (12-agent Workflow, fresh per-doc classification against the now-larger
  covering set) was dispatched and in flight at the time this checkpoint was written (pre-compact). Writing this now per
  the skill's "parked findings always get a durable issue doc" rule rather than risk losing it to context compaction
  before Phase 1/2/3 complete — will append Phase 1/2/3 results (orphan counts, any new Deferred items, batch2 draft if
  warranted) below once the Workflow returns.
