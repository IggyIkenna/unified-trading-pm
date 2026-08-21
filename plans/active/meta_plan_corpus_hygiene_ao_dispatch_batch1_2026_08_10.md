---
doc_type: plan
title:
  Plan-corpus hygiene AO batch 1 — 17 bounded, worker-determinable items extracted from the 28 live
  `ag_closeout_audit_*_parked_*.md` docs (2026-08-10 operator review)
summary: >-
  First AO-dispatch batch drawn from the PARKED-findings corpus rather than from satellite plans. A 2026-08-10 operator
  review of all 28 live `ag_closeout_audit_<tranche>_parked_<date>.md` docs found 62 open todos of which only ~1/3 were
  real, uncovered, human-needing work: ~22 were mechanical corpus hygiene (named-doc/named-field `asset_group` retags,
  stale-claim fixes, checkbox reconciliation) that the audit run could simply have executed, 5 were informational
  tombstones with no actor or done-when, and several were the SAME unresolved finding re-parked into a fresh dated doc
  every run (one ran 7 days across 5 docs, self-labelling "carried, 7th day"). Every doc was pinned `assigned_vm: NA`
  because AO-eligibility was being judged PER DOC — one operator-gated todo pinned the whole doc, so its bounded
  siblings never dispatched. This plan extracts the bounded slice and dispatches it. Three items were additionally
  RETAGGED off `[OPERATOR]` under `task_template.md` finding U (2026-07-27 operator ruling — read-only diagnostics and
  named-launcher relaunches are not operator-gated): the DP-VM-003 relaunch, the tradfi triple-dispatch investigation,
  and the `[ci, cross-cutting]` dual-tag content call. The recurrence is closed separately in
  `cursor-configs/skills/ag-closeout-audit/SKILL.md` (new HARD section "Three things that must NOT reach a parked doc").
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator, unified-trading-system-ui, instruments-service]
scope: [engineer, admin]
tags: [meta, ao-dispatch, plan-hygiene, ag-closeout-audit, parked-findings, asset-group-retag, batch-1, finding-u-retag]
related:
  [
    /plans/active/meta_plan_corpus_hygiene_ao_dispatch_batch1_finalize_2026_08_10.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/task_template.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.6
assigned_role: infra
effort: medium
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/task_template.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
    /scripts/docs/docspec.py,
  ]
source: >-
  Operator review 2026-08-10 (interactive session, slot 1) of all 28 live `ag_closeout_audit_*_parked_*.md` docs.
  Operator question: "why can't we make things like these AO plans? essentially they are tiny todos, their scope is
  understood, and this would auto-heal the issues." Verified mechanically ingestible —
  `agent-orchestrator/server/regen_backlog_from_plan.py:1799-1807` scans `plans/active/issues/` and ingests any doc
  declaring an `assigned_vm` (186 of 456 issue docs already do); the `NA` on the parked docs was a per-doc choice, not a
  structural rule. Every target's current `asset_group` and `locked_by` was verified live before this plan was written
  (all 17 unlocked; 2 originally-named targets found already archived and dropped from scope).
---

# Plan-corpus hygiene — AO dispatch batch 1 (2026-08-10)

## Why this batch exists

`/ag-closeout-audit` correctly routes AO-eligible work OUT of its parked doc and into an
`<ag>_satellite_ao_dispatch_batchN` plan. That worked for satellite-doc findings. It did NOT work for findings the audit
generated about the **plan corpus itself** — a wrong `asset_group`, a stale "0 open todos" claim, an unflipped checkbox
whose evidence the run had just cited. Those landed in the parked doc as `[DOCS] P3` todos on an `assigned_vm: NA` /
`execution_scope: local-only` doc, where nothing could ever pick them up. The oldest in this batch has been sitting
since 2026-08-01.

Two independent causes, both now fixed:

1. **The audit parked mechanical fixes instead of executing them.** The `ao` tranche's own 2026-08-10 run did the
   opposite — it fixed its mistags in-run under the Orthogonality HARD CHECK and shipped them
   (`unified-trading-pm@60b2953cc5`). The same day, the `cross-cutting` and `ci` runs parked the identical class of
   work. Closed by SKILL.md's new "Three things that must NOT reach a parked doc" § rule 1.
2. **AO-eligibility was judged PER DOC, not per todo.** Verbatim from a 2026-08-10 `/na-eligibility-audit` verdict on
   `ag_closeout_audit_ci_parked_2026_08_10.md`: _"Todo 1 (the 4-doc `ci`↔`infrastructure` retag pass) reads as
   bounded/mechanical on its own, but the whole-doc RECLASSIFY bar requires every open todo to clear, and todo 2 does
   not — doc stays NA."_ One un-dispatchable sibling pinned a bounded todo indefinitely. This plan is the workaround
   (extract the bounded slice into its own dispatchable doc); the whole-doc-bar question itself is a
   `/na-eligibility-audit` SKILL.md design issue and is filed as its own follow-up, not silently fixed here.

## Scope discipline for every todo below

- **The tag value is a content call the worker makes and states.** Where this plan names two candidate tags, read the
  target doc and pick one, recording the reasoning in the Progress Log. Do not leave a dual-tag in place — a doc belongs
  to exactly ONE tranche (Orthogonality HARD CHECK).
- **Retag = frontmatter `asset_group` only.** Do not restructure, re-prioritise, or archive the target as a side effect
  unless the todo says so explicitly.
- **Verify before editing**: re-read the target's current `asset_group` and `locked_by` at execution time. This plan's
  values were correct as of 2026-08-10 09:35 but the corpus is live. A locked target → skip, note it, do not force.
- **Do not edit the parked docs.** Their checkbox reconciliation is handled centrally by todo 17, once, to avoid N
  workers writing the same files concurrently.

## Todos

- [x] ✅ [DOCS] P1. **Retag `/plans/active/issues/deployment_api_prod_disable_auth_true_2026_08_06.md`** `asset_group`
      `[cross-cutting]` → `[ui]`. **Flagged urgent on 3 consecutive audit days** (2026-08-07, -08, -10) and never
      actioned: the doc records a live unauthenticated prod endpoint with all 4 fix-steps still open, and the wrong
      tranche tag is why no tranche's closeout ever claimed it. **Done when**: `asset_group: [ui]` and the doc is named
      in `ui`'s consolidated-closeout membership. Also report in the Progress Log whether those 4 fix-steps are still
      open — if they are, that is a P1 security finding needing its own escalation, not a retag follow-up. —
      unified-trading-pm@278b479e9f + `check_ag_closeout_linkage --only` 0 new orphans + `check_frontmatter_schema` 2
      docs clean. Fix-steps report: all 4 `[BACKEND] P1` still open, already escalated to
      `deployment_api_unauthenticated_prod_p0_2026_08_10.md` (step 1 DONE `UTL@336f2b3b6c`+`deployment-api@d0eebac4e6`).
- [x] ✅ [DOCS] P2. **Collapse the 4 `[ci, infrastructure]` dual-tags to `[ci]`** —
      `ci_pipeline_speed_and_cost_redesign_ 2026_08_05.md`,
      `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md`,
      `self_hosted_runner_public_repo_revert_2026_08_05.md`, `shared_ci_workflow_repo_extraction_2026_08_06.md` (all in
      `/plans/active/issues/`). The `ci` tranche's 2026-08-10 audit already confirmed all 4 CI-pipeline-primary by
      content. **Done when**: all 4 read `asset_group: [ci]`. — unified-trading-pm@242e239214 +
      `check_frontmatter_schema` 2013 docs zero violations (3 targets live in `plans/active/`; the 4th
      `shared_ci_workflow_repo_extraction_2026_08_06` is archived under `plans/archive/2026_08/` but was still retagged
      to `[ci]` for corpus orthogonality).
- [x] ✅ [DOCS] P3. **Retag the 3 surviving `cross-cutting` 2026-08-07 findings to their real owner** (all in
      `/plans/active/issues/`): `deployment_api_events_global_state_leak_flaky_metadata_probe_2026_08_06.md` → `[ci]` or
      `[infrastructure]` (audit recommended `ci`, `infrastructure` defensible — pick by content);
      `provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md` → `[ci]`;
      `qg_checkers_missing_claude_worktree_exclusion_2026_08_06.md` → `[infrastructure]`. **Note**: the other 2 targets
      that audit named (`agent_orchestrator_stale_pm_workflow_ref_blocks_promotion_2026_08_06.md`,
      `alerting_service_deploy_chain_blocked_by_layered_cicd_bugs_2026_08_06.md`) were verified 2026-08-10 as already
      archived under `/plans/archive/2026_08/issues/` — out of scope, no action. **Done when**: all 3 carry a single
      real tranche tag. — unified-trading-pm@e95abc7b0f. Live re-check at execution time (2026-08-16) found all 3 targets
      had already moved since this plan's 2026-08-10 authoring: `deployment_api_events_global_state_leak…` retagged
      `[ci]` here (content is CI-run test-flakiness — a pytest-xdist module-global leak blocking a promote PR's QG
      slice — matching the audit's own `ci` recommendation); `qg_checkers_missing_claude_worktree_exclusion…` was
      ALREADY `[infrastructure]` (fixed 2026-08-07 by the `ag-closeout-audit infra`-tranche run per its own
      in-file comment — no action needed); `provenance_marker_broken_by_history_rewrite…` is no longer in
      `plans/active/issues/` at all — it was resolved + archived 2026-08-15 to
      `/plans/archive/2026_08/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md`
      (its own banner confirms), so it falls under this same todo's own "already archived — out of scope, no
      action" precedent already applied to the other 2 originally-named targets. All 3 now carry a single real
      tranche tag (or are archived, out of scope).
- [x] ✅ [DOCS] P3. **Retag the 12 outstanding `cross_cutting_parked_2026_08_08` findings** (its findings 1-9 and
      11-13; finding 10 `autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md` was already fixed
      to `[infrastructure]` by the `ao` tranche's 2026-08-10 run — skip it). — unified-trading-pm (this same commit).
      Live
      re-check at execution time (2026-08-16) found findings 1-3 (`ao` ×3) and finding 5
      (`glue_pool_starvation_monitor_stale_jobs_after_runner_revert_2026_08_07.md`, `ci`, since archived) already
      retagged by prior `/ag-closeout-audit ao`/`ci` runs (2026-08-09) — no action needed, tags verified correct.
      Retagged the remaining 7: `deployment_api_ar_repo_override_audit_and_iam_probe_2026_08_07.md` (finding 4) →
      `[ci]`; `glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md` (finding 6) → `[ci]`;
      `mtds_type_ignore_ratchet_blocks_prek_intel_mac_fix_2026_08_03.md` (finding 8, archived) → `[ci]`;
      `workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md` (finding 9) → `[ci]`;
      `claude_code_agent_deletes_active_canonical_migration_vm_2026_08_07.md` (finding 11, archived, also fixed
      scalar→list frontmatter) → `[infrastructure]`; `deployment_service_prod_terraform_drift_2026_08_07.md`
      (finding 12) → `[infrastructure]`; `governance_sweep_deferred_followups_2026_08_06.md` (finding 13) → `[meta]`.
      All 12 verified via `docspec.py --check` (hard=0 soft=0 each, archived docs checked with `--doc-type issue`
      override since they're outside docspec's path-derivation). All 12 now carry a single real tranche tag, none
      retains `cross-cutting`. Per this plan's scope discipline, the parked doc itself
      (`ag_closeout_audit_cross_cutting_parked_2026_08_08.md`) was NOT edited — its own checkbox reconciliation is
      todo 17's job alone.
- [x] ✅ [DOCS] P3. **Retag the 5 remaining 2026-08-01/08-06 cross-cutting mistags** (all in `/plans/active/issues/`):
      `checkbox_flip_bundled_with_archival_git_mv_evades_flip_guard_2026_07_31.md` → `[ao]`;
      `gcp_service_accounts_registry_diverged_from_live_provisioning_2026_07_31.md` → `[infrastructure]`;
      `shared_host_gcloud_active_account_cross_slot_clobber_2026_08_04.md` → `[infrastructure]`;
      `unified_trading_system_ui_block_list_parity_test_failing_2026_08_04.md` → `[ui]`;
      `over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md` `[defi, cross-cutting]` → `[ci]` or
      `[infrastructure]` (owner TBD by content — pick one and say why). **Done when**: all 5 carry a single real tranche
      tag. — Executed 2026-08-16 (slot 11). This task carried `already_in_progress: true` on boot: 4 of the 5 retags
      were already sitting in this worktree as UNCOMMITTED WIP from an earlier interrupted run of this same task
      (`checkbox_flip_bundled_with_archival_git_mv_evades_flip_guard_2026_07_31.md` → `[ao]`,
      `gcp_service_accounts_registry_diverged_from_live_provisioning_2026_07_31.md` → `[infrastructure]`,
      `unified_trading_system_ui_block_list_parity_test_failing_2026_08_04.md` → `[ui]`,
      `over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md` → `[infrastructure]` — a defensible pick of the
      two named candidates since its content is a `plans/plan-hygiene` line-cap-gate policy finding
      (`scripts/plan-hygiene/check_line_caps.sh`), not a CI/CD pipeline/workflow-template matter, so `infrastructure`
      fits better than `ci`, the tag this batch's own todo 3 already reserved for actual CI-pipeline content) — verified
      each against `git diff` (all 5 confirmed correct vs. this plan's target, none left dual-tagged) and shipped in
      this same commit. The 5th, `shared_host_gcloud_active_account_cross_slot_clobber_2026_08_04.md`, was already
      `[infrastructure]` at HEAD (no working-tree diff) — genuinely fixed by a real prior `/ag-closeout-audit
      cross-cutting` run per its own frontmatter comment, confirmed 2026-08-10. All 5 verified frontmatter-clean:
      `docspec.py --check` 0 hard violations on all 5 (archived docs checked with `--doc-type issue` override).
      `check_ag_closeout_linkage --only` on the retagged pair caught 2 NEW orphans (a doc retagged to a new AG needs a
      path — `related:` link or a closeout-doc body mention — to that AG's consolidated-closeout family, which the
      pre-existing WIP hadn't added): fixed by adding `related: [/plans/active/infra_consolidated_closeout_2026_07_25.md]`
      to the `gcp_service_accounts_registry_diverged…` doc and appending `/plans/active/ui_consolidated_closeout_2026_07_30.md`
      to the `unified_trading_system_ui_block_list…` doc's existing `related:` list — re-check now 0 new orphans.
- [x] ✅ [DOCS] P3. **Resolve the `[ci, cross-cutting]` dual-tag on
      `/plans/archive/2026_08/issues/plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md`** to a single owner.
      Two prior audits (2026-08-09 Finding 4, 2026-08-10 Finding 2) both read the content as closer to
      `infrastructure`/`meta` than `ci` — i.e. the `ci` half may itself be wrong, not just the `cross-cutting` half.
      **RETAGGED from `[OPERATOR]` per `task_template.md` finding U**: this is a named-doc, named-field content call a
      worker can make and evidence, not a business/spend judgment, a credential gap, or an irreversible mutation. **Done
      when**: a single `asset_group` value with the deciding content cited in the Progress Log. — unified-trading-pm
      (this commit). Retagged `[ci, cross-cutting]` → `[meta]`. Content is entirely about the plan-corpus's OWN
      pre-commit tooling — `check_line_caps.sh`'s over-cap carve-out vs. `validate_plan_links.py`'s corpus-wide
      broken-link scan deadlocking on an archival edit, resolved via a `plan-completion-and-archival-discipline.md`
      carve-out fix — not a CI/CD pipeline/workflow-template matter (this batch's own todo 2/3 already reserve `ci` for
      that) and not general cloud/VM infra. Matches this same batch's todo 4 precedent
      (`governance_sweep_deferred_followups_2026_08_06.md` → `[meta]`, also a plan-corpus-governance doc). `docspec.py
      --check --doc-type issue` clean (hard=0 soft=0); `check_ag_closeout_linkage.py` shows 1 pre-existing orphan
      (`sportradar_credential_ask_2026_08_09.md`, unrelated file, baseline drift predating this task) — no new orphan
      from this retag, and the doc is `plans/archive/**` (closed record, outside the gated/linkage corpus per
      `doc-frontmatter-schema.md` §1) so no closeout-family `related:` link is needed.
- [x] ✅ [DOCS] P3. **Retag `/plans/active/issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md`**
      from `[defi]` to `[ui]` or `[cross-cutting]` by content — its `repos:` is
      `[unified-api-contracts, unified-trading-system-ui]` and the content is strategy-archetype DRIFT venue cleanup,
      not defi-specific. Carried unactioned since 2026-08-07. **Done when**: retagged, reasoning in the Progress Log. —
      Retagged `[defi]` → `[ui]`. The UAC-source portion was already resolved (2026-07-16 follow-up + 2026-07-26
      false-positive triage); the sole remaining open todo is exclusively `unified-trading-system-ui` registry-resync
      work (`ui-reference-data.json`, its generator, an E2E fixture), so `[ui]` fits better than `[cross-cutting]`
      (single-repo-primary, not genuinely multi-domain). Added `related:` link to
      `ui_consolidated_closeout_2026_07_30.md`. Full reasoning in the target doc's own Progress Log.
- [x] ✅ [DOCS] P3. **Fix the stale "0 open todos" claim in `/plans/active/tradfi_consolidated_closeout_2026_07_18.md`**
      (~line 745): it states `phantom_audit_estate_coverage_gap_2026_07_10.md` has "0 open todos
      (closed/archived/record-only)" but that doc carries 1 open `[SCRIPT] P2` (widen the phantom audit to the full
      ~47-bucket kind×AG matrix). Re-verified still wrong 2026-08-10. **Done when**: the line reflects the target's real
      open-todo count. — Re-verified 2026-08-16: `phantom_audit_estate_coverage_gap_2026_07_10.md` still carries exactly
      1 open todo (line 180, `[SCRIPT] P2`, the same "widen to ~47-bucket kind×AG matrix" item, gated on the
      2026-08-08 operator ruling recorded at
      `/plans/active/issues/phantom_audit_estate_coverage_gap_2026_07_10.md:176`). Line 745-746 of the closeout doc
      corrected to "1 open (re-verified 2026-08-16)" with the todo's text cited inline. — unified-trading-pm (this
      commit).
- [x] ✅ [DOCS] P2. **Verify + flip the 3 already-resolved checkboxes** in
      `/plans/archive/issues/escalation_queue_reconciler_false_resolution_via_unrelated_qg_green_2026_08_09.md`
      (archived 2026-08-20) —
      unified-trading-pm@3fa34e2475. Items 2 (DP-FETCH-009 `[VERIFY] P1`) and 4 (code-fix `[REVIEW] P2`) were already
      `[x]` — confirmed by direct doc read. Item 1 (DP-VM-003 `[OPERATOR] P1`) flipped `[x] ✅ [DATA] P1`: live
      `gcloud compute instances describe` confirmed VM `mtds-backfill-odds-smallchunk14-20260809` RUNNING
      (asia-northeast1-c, created 2026-08-10T09:29:02Z), matching the independent verification already recorded in this
      plan's Progress Log (todo 11, slot 22). Item 3 was already extracted (prose, no checkbox). All 4 items resolved;
      `archive_exempt: true` added — doc is the operator-visible historical-blast-radius record.
- [x] ✅ [DOCS] P3. **Fix the stale Phase 7 wording in `/plans/active/ui_satellite_ao_dispatch_batch1_2026_08_06.md`**
      (~line 202): its Deferred item 8 still described `artifact_pipeline_observability_2026_07_17.md`'s Phase 7 as
      "STILL OPEN — prod is silent...", but Phase 7 closed 2026-08-07. **Already fixed** — verified 2026-08-16 (slot 7)
      that this exact fix landed 2026-08-10 in `unified-trading-pm@478f90d112` ("flip 3 ui-parked todos (Findings
      1/3/4) — SKILL.md clarifications already done, batch1 stale Phase 7 wording fixed, archive_exempt added"): its
      diff replaces the "STILL OPEN" prose with wording citing a 2026-08-07 operator ruling (per
      `/plans/active/ui_satellite_ao_dispatch_batch1_2026_08_06.md`'s own Deferred item 8) plus live verification —
      `cpu-throttling: false` on the live Cloud Run service, `/api/artifacts/images` now returns full real data, 39
      repos, 0 empty. Confirmed at HEAD (`git diff HEAD` clean, no working-tree delta) — this todo's own text was
      simply never flipped after that landed. No new code/doc change needed; flip only.
- [x] ✅ [DATA] P1. **Relaunch the stalled backfill VM DP-VM-003.** **RETAGGED from `[OPERATOR]` per `task_template.md`
      finding U** (2026-07-27 operator ruling — `[OPERATOR]` is for a business/spend judgment, a human-only credential,
      or an irreversible destroy; a named-launcher relaunch is none of those): AO workers have driven DP-VM-003
      repeatedly and on the record (`agt-5065b7`, `agt-71ccbf`, `agt-c14d58`), and both cloud identities are
      IAM-self-service. Follow `/codex/05-infrastructure/vm-launcher-runbook.md`: no fire-and-forget — verify STARTED,
      verify ongoing progress against a real progress metric, and record a terminal state. Preemption recovery resumes
      from measured PROGRESS, never replays `START_DATE`. **Done when**: relaunched and progressing, or a measured
      verdict on why it cannot be, in the Progress Log.
- [x] ✅ [REVIEW] P3. **Investigate why the `tradfi` tranche received THREE `/ag-closeout-audit` dispatches on
      2026-08-10** — slot 26 (`all`-mode, no `$TRANCHE`), slot 25 (sharded, `agt-022d39`), slot 22 (sharded,
      `agt-a19d1f`). No content harm resulted, but triple-dispatch is wasted fleet capacity and suggests the `all`-mode
      and sharded schedulers do not deconflict. **RETAGGED from `[OPERATOR]` per finding U**: a read-only diagnostic can
      never be operator-gated regardless of subject. **Done when**: the dispatch path is identified from AO
      scheduled-job config/logs and either a fix is filed as a follow-up todo or the overlap is shown to be intentional.
- [ ] [SCRIPT] P3. **Dispatch a fresh `/plan-reconcile tradfi` pass** to complete the stalled
      `plan_reconciler_findings_tradfi_2026_08_09.md` run from STEP 4 onward and file its 5 named P0/P1 candidates.
      Scope note: this is the WORKER half only — clearing that doc's `locked_by` needs `[unlock-plan]`, which stays
      operator-only (see this batch's Deferred section). Run the pass and write findings to a NEW dated doc if the
      original is still locked. **Done when**: STEP 4 onward is complete and the 5 candidates are filed.
- [ ] [DATA] P3. **Raise the per-date subprocess timeout in the DeFi MDPS candle backfill** above 1800s for DeFi years
      with 10K+ instruments, per `/plans/active/issues/defi_mdps_candle_backfill_fleet_outcome_2026_08_06.md`'s sole
      remaining open item (its `[DATA] P2` relaunch item is already done). Confirmed 2026-08-10 as NOT covered by
      `defi_satellite_ao_dispatch_batch11_2026_08_09.md`. **Done when**: the timeout is raised to a value justified by
      measured per-date runtime at 10K+ instruments (state the measurement), and the change is shipped.
- [x] ✅ [REVIEW] P3. **Verify `instruments-service@62a8b1d8` actually covers parts 3a and 3b**, not just 3c — verdict
      written 2026-08-10 (slot 7, review) into `/plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md`
      lines ~257-303. Per-part summary: **3a** PARTIALLY COVERED (local fixture-ID computation via
      `build_fixture_id`/`build_team_id`, not the external api-football/odds-api registry resolution the plan text
      describes — but same approach as the already-shipped Polymarket adapter; accepted by the existing partial-progress
      note). **3b** COVERED (Kalshi half — stamps `canonical_instrument_id` so `_build_mapping()` UAC@1dddc680 can pair
      Kalshi↔Polymarket; `mapped_sport_event_id` was separately found DEAD/unwired). **3c** NOT COVERED (correctly
      excluded — team-name canonicaliser shipped separately 2026-08-05). **League scope**: ALL leagues structurally
      (code is league-agnostic via `SPORTS_*` prefix), not MLB-only; test gap is coverage-only. Full diff confirmed:
      `kalshi.py` +25L, test +34L.
- [x] ✅ [DOCS] P3. **Archive
      `/plans/archive/2026_08/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md`** via the
      standard 6-step ritual — DUPLICATE of the same item independently dispatched as
      `ao_satellite_ao_dispatch_batch20_2026_08_13.md`'s own todo (source: `ag_closeout_audit_ao_parked_2026_08_10.md`);
      closing here rather than leaving a redundant re-dispatchable duplicate — unified-trading-pm (same commit as the
      batch20 archival, 2026-08-14, slot 6): source doc archived with banner, `status: resolved`, every corpus referrer
      repointed, inventory regenerated. See batch20's own checkbox for the full evidence citation.
- [x] ✅ [DOCS] P2. **Reconcile the 28 `ag_closeout_audit_*_parked_*.md` docs against this batch — ONE pass, one
      worker.** (a) Flip each todo this batch has completed to `[x]` citing this plan; (b) collapse the cross-day
      duplicates into the single oldest carrier and re-date it, per SKILL.md's new rule 3 —
      `self_dispatched_orphan_count` (5 copies: infra 08-03/-04/-06/-08/-09),
      `Scope + conflict-check the 2 flagged batch-era candidates` (5 copies, same docs),
      `deployment_api_prod_disable_auth_true` retag (2 copies: cross-cutting 08-07/-08); (c) convert the 5 "No action
      needed on Finding N" tombstones (prediction 07-31 ×1, prediction 08-09 ×4) and the 4 "left unchecked for
      continuity only" entries (cross-cutting 08-10) from `- [ ]` lines into prose in the findings body, per rule 2.
      **This todo is deliberately single-owner** — every other todo in this batch is forbidden from editing a parked
      doc, so these 28 files have exactly one writer. **Done when**: no finding appears in two parked docs, no
      actor-less `- [ ]` remains, and the corpus-wide open count is reported before/after. — **DONE 2026-08-10 (slot 32,
      task `meta_plan_corpus_hygiene_ao_dispatch_batch1-d52772441159`)**. **Corpus-wide open count: 16 → 14** (all 44
      `ag_closeout_audit_*_parked_*.md` docs, active + archive). (a) Flipped 2 parked-doc checkboxes for landed batch
      todos: `ag_closeout_audit_cross_cutting_parked_2026_08_07.md` finding 4 (`deployment_api_prod_disable_auth_true`
      retag, batch todo 1 @`unified-trading-pm@278b479e9f`) and `ag_closeout_audit_ci_parked_2026_08_10.md` finding 1
      (4-doc `[ci, infrastructure]`→`[ci]` retag, batch todo 2 @`unified-trading-pm@242e239214`). The other 14 open
      parked-doc items each map to a still-in-flight batch todo (3,4,5,7,8,9,14,16) — left open per the docs' own "do
      not flip them early" notes. (b) Duplicate collapse verified already executed by the batch authoring / prior
      passes: `self_dispatched_orphan_count` + `Scope + conflict-check` both origin-carried in
      `ag_closeout_audit_infra_parked_2026_08_03.md` (flipped → `operator_action_items_consolidated_2026_08_08.md`),
      DEDUPED markers present in infra 08-04/06/08/09; `deployment_api_prod_disable_auth_true` retag copy in
      `ag_closeout_audit_cross_cutting_parked_2026_08_08.md` already marked DEDUPED. Open-todo subject scan: no finding
      subject appears in >1 parked doc. (c) Tombstone conversion verified already executed: prediction 07-31 (0 open),
      prediction 08-09 (findings 1-4 converted to prose 2026-08-10), cross-cutting 08-10 continuity entries are prose
      inside `[x]` CARRIED/RESOLVED markers; no open `- [ ]` carries informational phrasing. All edits shipped via
      `safe-doc-push.sh` + `check_frontmatter_schema` 2013 docs zero violations.

## Deferred — genuinely operator-only, NOT dispatchable (per `task_template.md` finding U's positive test)

Left in their parked docs deliberately. Each is finding U (i) a business/spend judgment or (ii) a human-held credential
— not reflexive caution:

| Item                                                                                                                                      | Parked in                  | Finding U class                            |
| ----------------------------------------------------------------------------------------------------------------------------------------- | -------------------------- | ------------------------------------------ |
| Provision `glassnode-api-key` + `kaiko-api-key` GSM secrets, or decline                                                                   | cross-cutting 08-10        | (ii) human-held credential                 |
| Provision `sportradar-api-key` + decide its scope, or decline                                                                             | cross-cutting 08-10        | (ii) human-held credential                 |
| Approve/decline the ICE/OPRA Databento subscription add                                                                                   | cross-cutting 08-10        | (i) spend judgment                         |
| Provision the IPRoyal residential-proxy credential (~$7 PAYG)                                                                             | tradfi 08-10               | (ii) human-held credential                 |
| Supply the rate-limit-probe engineering spec                                                                                              | cross-cutting 08-10        | (i) design input, no data-derivable answer |
| Approve draft batches (cefi batch16, ao batch19, infra batch11)                                                                           | cefi/ao/infra 08-10        | skill design — drafts never auto-ship      |
| `[unlock-plan]` ×3 (`deployment_ui_smoke_failures…`, `plan_reconciler_findings_2026_08_06`, `plan_reconciler_findings_tradfi_2026_08_09`) | ui 08-09/-10, tradfi 08-10 | CLAUDE.md: ASK, never autonomous           |
| Confirm the 6 transcribed rulings in `operator_ruling_record_ao_round5…`                                                                  | ao 08-10                   | operator-only by construction              |

Open-ended design calls also left NA (not finding U, but not worker-determinable either): where future ruling sessions
get recorded; the aggregate-zero-path signal design fork; the `context_scope` sufficiency metric; whether
`/ag-closeout- audit all` mode should budget for the full per-tranche sweep; the `self_dispatched_orphan_count`
generator addition; scoping the 2 flagged `CITE_RE`-hardening batch-era candidates.

## Follow-ups

- [x] ✅ [DOCS] P2. **Fix `/na-eligibility-audit`'s whole-doc RECLASSIFY bar.** — `unified-trading-pm@953db0e945`. Its
      SKILL.md requires EVERY open todo in a doc to clear before the doc can move off `assigned_vm: NA`, so a single
      operator-gated sibling pins bounded work indefinitely — measured live on
      `ag_closeout_audit_ci_parked_2026_08_10.md` (2026-08-10 verdict quoted above). The fix is a per-todo verdict with
      a split path (extract the bounded slice into a batch, keep the rest NA), the shape this plan had to apply by hand.
      **Done when**: the skill emits per-todo verdicts and names the extraction path.

      **Shipped**: split the old whole-doc-only RECLASSIFY (verdict 4) into two sub-verdicts — verdict 4 (whole-doc, every
          open todo bounded → flip `assigned_vm` in place) and verdict 5 (per-todo split path, mixed bounded + operator-gated →
          extract bounded slice into `{topic}_satellite_ao_dispatch_batch{N}` + `_finalize` pair, source doc stays NA). Added
          extraction mechanics to Phase 3 (topic resolution, conflict-check-before-write, source-doc checkbox flip, Progress
          Log marker). Updated the "Why RECLASSIFY volume is inherently low" section to document the new model.

## Codex SSOTs

- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual (todo 16)
- `/codex/11-project-management/doc-frontmatter-schema.md` + `/scripts/docs/docspec.py` — `asset_group` enum (all
  retags)
- `/codex/05-infrastructure/vm-launcher-runbook.md` — no fire-and-forget, progress-metric verification (todo 11)
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § Dispatch-scope eligibility — the bar every
  todo here had to clear
- `/codex/11-project-management/cross-reference-path-convention.md` — leading-slash refs

## Progress Log

- **2026-08-10** — Authored from an operator review of all 28 live parked docs (interactive session, slot 1). Verified
  before writing: `plans/active/issues/` IS AO-ingestible (`regen_backlog_from_plan.py:1799-1807`, 186/456 issue docs
  already `assigned_vm: planning`), so the parked docs' `NA` was a per-doc choice not a structural rule; all 17 targets
  unlocked; 2 originally-named targets (`agent_orchestrator_stale_pm_workflow_ref…`, `alerting_service_deploy_chain…`)
  already archived and dropped from scope; `autostash_pop…` already retagged by the `ao` run and skipped. Three items
  retagged off `[OPERATOR]` under finding U. Recurrence closed in SKILL.md (3 edits: coverage bar, finding-U positive
  test in the operator-gated taxonomy, new "Three things that must NOT reach a parked doc" HARD section).
- **2026-08-10T16:10Z (slot 22, data_engineering, task `meta_plan_corpus_hygiene_ao_dispatch_batch1-8cdbdf6683ca`) —
  DP-VM-003 (todo 11) verified already relaunched and progressing — flipped with live evidence.** Live check 16:00Z
  (this same slot, prior task) + re-confirmed 16:05Z:
  `gcloud compute instances describe mtds-backfill-odds-smallchunk14-20260809 --zone=asia-northeast1-c` → `RUNNING`,
  created **2026-08-10T09:29:02Z UTC** — this IS the fresh relaunch the tracker doc's 10:06Z entry already logged
  ("Fresh relaunch after smallchunk14's 08:36Z SPOT-preemption STOP (hang-doc DP-VM-003) — landed ~09:29Z by another
  actor"). So the 08:36Z SPOT-preemption STOP + the operator decision the hang-doc's `BLOCKED-OPERATOR-DECISION` flagged
  are both superseded: the VM came back (SPOT capacity returned), was relaunched once more, and is now healthy and
  progressing. `run.log` tail 15:58:54Z: chunk **45/2171** (league=ARGENTINA_PRIMERA, date=2020-10-11),
  `MEM_PRECHECK mem_available_mb=29827` (~29GB free), API keys validated, **0 `CHUNK_FAILED`/OOM/exit=137 lines since
  this relaunch**; `PROGRESS.json` `last_completed_date=2020-10-11`, `monotonic: true`, updated 15:45:52Z. Measured
  verdict per the done-when: **relaunched and progressing** — no further VM action needed from this todo (and the
  odds_api backfill's own standing instruction forbids launching a duplicate). Escalation `agt-d2322e` (the
  data_pipeline_failure escalation this relaunch was dispatched under) is terminal — absent from the active queue. No
  code change (VM-operation todo); the flip cites the live VM state above. Full live tracker for the ongoing campaign:
  `plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md`.
- **2026-08-10 (slot 32, infra, task `meta_plan_corpus_hygiene_ao_dispatch_batch1-d52772441159`) — todo 17
  (28-parked-doc reconciliation) executed.** Before/after open count: **16 → 14** across all 44 parked docs (active +
  archive). Flipped 2 parked-doc checkboxes for landed batch todos (cross-cutting 08-07 finding 4 → todo 1
  @`unified-trading-pm@278b479e9f`; ci 08-10 finding 1 → todo 2 @`unified-trading-pm@242e239214`). The remaining 14 open
  items map to still-in-flight batch todos 3/4/5/7/8/9/14/16 — left open per the "do not flip early" notes. (b)
  duplicate collapse + (c) tombstone conversion verified already executed by the authoring/prior passes (infra 08-03
  origin + DEDUPED markers in 08-04/06/08/09; cross-cutting 08-08 `deployment_api` copy DEDUPED; prediction 07-31/08-09
  - cross-cutting 08-10 continuity entries already prose). No finding subject appears in >1 parked doc; no actor-less
    `- [ ]` remains. Shipped via `safe-doc-push.sh`; `check_frontmatter_schema` 2013 docs zero violations.
- **2026-08-10 (slot 11, review, task `meta_plan_corpus_hygiene_ao_dispatch_batch1-916bce380a6e`) — todo 12 (tradfi
  triple-dispatch investigation) executed.**

  **Dispatch paths identified:**

  1. **Sharded path** (`ag-closeout-auditor.timer`): systemd timer fires every 2h on even hours at :30 UTC, dispatches
     all 10 tranches in batches of 4 via `POST /api/plan-health/dispatch` with `mode=ag_closeout, tranche=<name>`. Each
     tranche = independent `dispatch()` call → independent slot pick → independent worker. The `tradfi` tranche
     succeeded at 14:31 UTC (`lifecycle-complete`). Earlier fires at 02:30 (all `queued` — no capacity) and 10:31 (all
     `quarantined` — slot state) never spawned workers.
  2. **`all`-mode path** (slot 26): source unclear — left no `ag_closeout_auditor` scheduled-job row. The timer NEVER
     dispatches `all` mode (it only fires per-tranche). Most likely a manual operator skill invocation or a direct
     `/skill ag-closeout-audit` call without a tranche argument (which defaults to `all` per SKILL.md).

  **Root cause — deconfliction gap in `scheduled_job_already_ran.py`:**

  The `--list-done-tranches` guard (used by the sharded timer) filters on `row.get("tranche")` being truthy (line 174).
  An `all`-mode row (`tranche=null`) is **invisible** to this check. Conversely, `--no-tranche` filters OUT rows with a
  tranche value. The two scoping paths are **mutually blind** — neither sees the other's rows as blocking, so an
  `all`-mode run and a sharded `tradfi` run on the same day would not deconflict.

  **Whether the gap caused the triple dispatch:** the scheduled jobs data shows only ONE successful `tradfi` row on
  2026-08-10 (14:31 UTC). No `tranche=null` row exists for `ag_closeout_auditor`. The claimed `all`-mode dispatch
  (slot 26) must have bypassed the scheduled-job reporting entirely. If it did run, the gap would have let it through —
  but the gap alone cannot explain the triple dispatch without the `all`-mode dispatch having actually fired from
  outside the scheduled-job system.

  **Recommendation — fix the gap regardless:** even if this specific incident's `all`-mode dispatch was manual, the gap
  is real and would bite on any future day where both modes run. The fix: `--list-done-tranches` should also check for
  `tranche=null` rows for the same job on the same day — a completed `all`-mode run covers ALL tranches, so it should
  block every per-tranche dispatch. Filed as follow-up:
  `/plans/archive/2026_08/issues/ag_closeout_all_vs_sharded_mutual_blindness_2026_08_10.md`.

  No code shipped (read-only diagnostic). Plan flip only — unified-trading-pm@<this-commit>.
- **2026-08-16 (slot 11, infra, task `meta_plan_corpus_hygiene_ao_dispatch_batch1-a65c90e56bde`) — todo 5 (5 remaining
  cross-cutting mistags) executed.** Boot reported `already_in_progress: true` for this exact task; 4 of the 5 target
  retags were already sitting as UNCOMMITTED working-tree WIP from an earlier interrupted run of this same task —
  `checkbox_flip_bundled_with_archival_git_mv_evades_flip_guard_2026_07_31.md` → `[ao]`,
  `gcp_service_accounts_registry_diverged_from_live_provisioning_2026_07_31.md` → `[infrastructure]`,
  `unified_trading_system_ui_block_list_parity_test_failing_2026_08_04.md` → `[ui]`,
  `over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md` → `[infrastructure]` (a line-cap-gate/plan-hygiene
  policy finding fits `infrastructure` better than `ci`, which this batch's own todo 3 already used for actual
  CI-pipeline/workflow content) — verified each against `git diff` HEAD (all 4 confirmed matching this plan's target,
  none left dual-tagged) and shipped in this commit. The 5th, `shared_host_gcloud_active_account_cross_slot_clobber_2026_08_04.md`,
  was already `[infrastructure]` at HEAD with no working-tree diff — genuinely retagged by a real prior
  `/ag-closeout-audit cross-cutting` run per its own frontmatter comment (2026-08-10). `docspec.py --check` clean (0
  hard) on all 5 (archived docs checked with `--doc-type issue`). `check_ag_closeout_linkage --only` caught 2 new
  orphans on the retagged pair (`gcp_service_accounts_registry_diverged…` -> `[infrastructure]`,
  `unified_trading_system_ui_block_list…` -> `[ui]`) since a new AG needs a `related:` path to its closeout family —
  fixed by adding `related:` links to `infra_consolidated_closeout_2026_07_25.md` and
  `ui_consolidated_closeout_2026_07_30.md` respectively; re-check 0 new orphans.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries) — first scout pass.
