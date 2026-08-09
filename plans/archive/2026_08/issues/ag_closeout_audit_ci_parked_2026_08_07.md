---
doc_type: issue
title: ag-closeout-audit ci parked findings — 2026-08-07 (SUPERSEDED — see 2026-08-08 final report)
summary: >-
  Parked findings from the scheduled ag_closeout_auditor run (2026-08-07, tranche=ci, slot 4), captured mid-run via
  /pre-compact before Phase 1's 46-agent classification Workflow (run wf_1f04b9b2-680) returned. 4 findings so far, all
  from Phase 0 discovery: 6 docs dual-tagged [ci, infrastructure] (informational, not ci's to unilaterally retag), 1 doc
  dual-tagged [sports, ci] (informational, sports-owned), 1 asset_group:[meta] doc that reads ci-scoped (fold-in
  candidate), and a check_ag_closeout_linkage.py ratchet regression observation (71 vs baseline 69). **SUPERSEDED
  2026-08-08**: `wf_1f04b9b2-680` was not resumable cross-session, so the 2026-08-08 run re-derived the candidate set
  fresh and completed Phase 1-3 in `ag_closeout_audit_ci_parked_2026_08_08.md`, which carries the full orphan-count
  report + the resulting `ci_satellite_ao_dispatch_batch6_2026_08_08.md` draft. All 4 findings below are re-confirmed
  unchanged there.
status: resolved
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ag-closeout-audit, parked, ci, orphan, mistag, interim]
related:
  [
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch5_2026_08_02.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: 2026-08-07
parent_epic: infrastructure_master
assigned_vm: NA
priority: P3
last_updated: 2026-08-08
source: >-
  ag_closeout_auditor scheduled run 2026-08-07 (tranche=ci, slot 4, DISPATCH_ID=agt-d12c5d) — captured mid-run by
  /pre-compact ritual while Phase 1's Workflow (run wf_1f04b9b2-680, 46 candidate docs) was still executing.
resolved_by: ag_closeout_audit_ci_parked_2026_08_08
superseded_by: ag_closeout_audit_ci_parked_2026_08_08
locked_by:
execution_scope: orchestrator-agent
drift_direction: none
depends_on: []
---

# ag-closeout-audit ci parked findings — 2026-08-07 (INTERIM)

> **This doc is INTERIM.** Phase 0 (covering-plan discovery + candidate inventory, 45 docs + 1 meta fold-in candidate)
> is complete. Phase 1 (per-doc classification, 46-agent `Workflow`, run id `wf_1f04b9b2-680`) was dispatched and still
> running when this checkpoint was written. Phase 2 (synthesis/report) and Phase 3 (conflict-check + possible batch6
> draft) have not run yet. **Append** the final orphan-count report and any batch6/finalize decision to THIS doc (same
> day, same run) rather than creating a second `ag_closeout_audit_ci_parked_2026_08_07.md` — per the skill's own
> one-doc-per-tranche-per-run + append rule.

## Phase 0 summary (for context)

Covering-plan set: `ci_consolidated_closeout_2026_07_25.md` (archived 2026-07-28, pure reachability digest, superseded
in effect by the batch chain) + `ci_satellite_ao_dispatch_batch1_2026_07_26.md` (1 open/42 done) + `..._batch1_finalize`
(4 open, gated) + `..._batch4_2026_07_31.md` (1 open/8 done) + `..._batch4_finalize` (4 open, gated) +
`..._batch5_2026_08_02.md` (3 open/3 done) + `..._batch5_finalize` (4 open, gated); archived
`..._batch2_2026_07_29.md`/`_finalize` (14/14, 4/4 done) + `..._batch3_2026_07_30.md` (1/1 done) already fully executed.
`generate_ag_closeout_audit_candidates.py --tranche ci`: **45 members, 7 never-cited** in an active covering doc. Prior
runs (2026-08-03: 40 members/7 never-cited, 0 new batch6 candidates; 2026-08-04: 42 members/4 never-cited, full 42-agent
Phase 1 sweep, 31 orphaned but 0 AO-eligible, 0 new batch6 candidates, second day running) are recorded in
`ci_satellite_ao_dispatch_batch5_2026_08_02.md`'s own Progress Log — read that first, this run re-verifies rather than
re-derives.

## Finding 1 (informational) — 6 docs dual-tagged `[ci, infrastructure]`, likely a systemic authoring mistag

All `parent_epic: infrastructure_master`, all dated 2026-08-03 through 2026-08-06 (recent):

- `/plans/archive/2026_08/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`
- `plans/active/ci_pipeline_speed_and_cost_redesign_2026_08_05.md`
- `plans/active/fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md`
- `plans/active/self_hosted_runner_public_repo_revert_2026_08_05.md`
- `plans/active/shared_ci_workflow_repo_extraction_2026_08_06.md`
- `plans/active/issues/client_reporting_api_promote_wedge_backmerge_dead_2026_08_06.md`

Content (titles + summaries read at Phase 0) is CI/CD-pipeline-internal in every case (CI runner VM fleet, GH Actions
workflow-template dedup/extraction, self-hosted-runner policy, LDR→main promotion wedge) — `infrastructure` looks like
the extraneous tag, `ci` the correct one, mirroring the exact pattern the 2026-08-04 run already flagged on the first of
these six (`ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`, see that doc's own Progress Log entry) and
explicitly declined to retag unilaterally: `parent_epic: infrastructure_master` does not cleanly disambiguate (it feeds
BOTH `ci` and `infra` tranches per the skill's own classification-mechanism section), and a non-owning-tranche write
risks a race with a concurrently-running `infra`-tranche worker (`per-tab-worktrees.md` § "What worktree isolation does
NOT cover" — `git stash` isn't the only shared-clone hazard; an unarbitrated frontmatter write on a doc two sharded
workers both consider "maybe theirs" is the same class of risk). **Not acted on here for the same reason.**

**Recommendation**: a dedicated corpus-wide `ci`↔`infrastructure` retag pass (mirroring
`asset_group_ao_ci_infra_schema_expansion_2026_07_27.md`'s methodology) once both tranches' owners are available to
adjudicate together, OR the `infra` tranche's own audit run resolves it directly if it reads the same way. Full Phase 1
verdicts for these 6 (orphan status, not just tag) are pending in the in-flight Workflow run.

## Finding 2 (informational) — `[sports, ci]` dual-tag, sports-owned, likely `ci` is the mistag

`plans/active/issues/ag_closeout_audit_sports_tooling_followups_2026_08_06.md` — `parent_epic: sports_master`, authored
BY a 2026-08-06 sports-tranche audit run. Its 2 todos are about `check_ag_closeout_linkage.py`
(`scripts/plan-hygiene/`), a plan-hygiene/tooling-gate bug, not CI/CD-pipeline mechanics (quickmerge, Cloud Build/GitHub
Actions, SIT/promotion, release-tag machinery — this tranche's declared scope per its own consolidated closeout doc).
`infrastructure` or `ao` (the check backs the ag-closeout-audit skill's own machinery) both read closer than `ci`.
**Primary owner is sports (parent_epic) — not retagged here, not ci's to write.**

**Recommendation**: flag for the `sports` tranche's own audit (or a human) to correct the secondary tag; low priority
(P3), doesn't block anything.

## Finding 3 (informational) — `asset_group: [meta]` doc reads ci-scoped: `quality_gates_quickmerge_timing_baseline_2026_07_31.md`

Tagged bare `[meta]`, `parent_epic: orchestrator_master`, `assigned_role: infra` — but its content (measuring
`quality-gates.sh`/`quickmerge.sh` wall-clock timing, single-host vs planning-vm) matches this tranche's own declared
Track 1 (quickmerge mechanics) / Track 5 (build/test tooling + CI-cost) scope reasonably well, though the orchestrator
parent_epic and infra role also have a claim. Per the skill's Phase 0.3 "meta sweep" rule ("any single-tranche run MUST
still sweep `asset_group: meta` and fold genuine hits into whichever of ci/infra/ao/cross-cutting its content actually
matches"), this doc was added to the in-flight Phase 1 Workflow as a 46th candidate with an explicit tag-judgment
instruction; verdict pending.

## Finding 4 (informational) — `check_ag_closeout_linkage.py` ratchet regression: 71 vs baseline 69

Ran the mechanical linkage gate as a cross-check (`scripts/plan-hygiene/check_ag_closeout_linkage.py`, corpus-wide, not
ci-only): 71 orphans vs a baseline of 69 (2 above baseline, exit 0 — advisory in this invocation). 7 of the 71 carry
bare `asset_group: [ci]` (the gate only checks single-tag docs, so it's blind to the Finding-1/2 dual-tag docs
entirely): `breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md`,
`deployment_api_mtds_meta_missing_blocks_workspace_qg_step_5_83_2026_08_03.md`,
`pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md`,
`quality_gates_v2_concurrency_and_bookkeeping_job_cost_2026_08_02.md`,
`workflow_template_drift_repeated_during_phase7_rollout_2026_07_27.md`, `monitoring_control_plane_master_2026_06_10.md`,
`test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md` — all 7 are already in the in-flight Phase 1 candidate
list, so their REAL orphan status (per this skill's fuller batch1/4/5-Deferred-table-aware methodology, not the gate's
cruder "mentioned in the closeout digest's own body text" check) is pending there. **Verified at least one is a gate
false-positive, not a real gap**: `pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md` IS tracked (batch4 D4-10

- its own "Escalated to the operator" question 1) — the gate's "closeout family" for `ci` is only
  `ci_consolidated_closeout_2026_07_25.md` itself (a short archived digest that explicitly does NOT enumerate every
  satellite doc by name), not the batch1/4/5 Deferred tables where the real tracking lives, so it under-counts coverage
  by design for this tranche. Whether the 71-vs-69 regression's 2 NEW-since-baseline violations are ci-owned is not yet
  determined (baseline is corpus-wide, not per-tranche) — out of this run's scope to chase further; noting for
  `/plan-reconcile` or whoever owns the ratchet.

---

**Parked count reconciliation (INTERIM — not final)**: 4 findings written to this doc so far, all Phase-0-discovered and
independent of Phase 1's per-doc verdicts. **0 of these 4 are genuine orphaned-AO-eligible-work findings** — all 4 are
tag-correctness/gate-cross-check observations, not extractable batch todos. Phase 1's actual orphan/coverage verdicts
(and any genuine new parked findings among the 46 candidates) will be appended here once the workflow completes.

---

**na-eligibility-audit 2026-08-07** (tranche `ci`, autonomous, `agt-cbbd1f`): KEEP-NA, valid — this is a DIFFERENT
skill's (`ag-closeout-audit`) own interim checkpoint doc, not orphaned/dispatchable content in its own right. 0
checkbox-style todos (all 4 findings are prose/informational, explicitly "not extractable batch todos" per the doc's own
reconciliation line above). `assigned_vm: NA` is correct for a findings-tracker awaiting its own Phase 1-3 completion —
not this audit's to reclassify or archive. No edits to Phase 0-4 content; this note only.
