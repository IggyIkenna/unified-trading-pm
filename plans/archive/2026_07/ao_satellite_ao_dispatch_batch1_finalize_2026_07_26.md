---
doc_type: plan
title: AO satellite AO batch 1 — finalize
summary: >-
  Gated closeout for ao_satellite_ao_dispatch_batch1_2026_07_26.md — machine-held via depends_on + gate_on_depends until
  every todo in that batch is done. Reconciles each completed todo's evidence back into its TRUE source issue doc (the
  batch was an extraction, so the source docs' own checkboxes are the ones that go stale), re-checks whether any
  Deferred item's gate has since cleared, archives the source docs that reach zero open todos, and runs the standard
  6-step archival ritual on the batch plan itself.
status: complete
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-1, finalize]
related:
  [
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-30"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
assigned_role: review
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_satellite_ao_dispatch_batch1_2026_07_26]
gate_on_depends: true
sequential: true
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored in
  the same turn as its batch by the /ag-closeout-audit skill run of 2026-07-26.
---

# AO satellite AO batch 1 — finalize

> **🟢 ARCHIVED 2026-08-01** — all 5 todos `[x]`, `locked_by:` empty. Batch 1 re-verified + evidence reconciled,
> Deferred items re-checked (2 spun into `/plans/active/ao_satellite_ao_dispatch_batch2_2026_08_01.md`), 1 net-new
> resolved doc found + archived (`escalation_backlog_repo_collision_blind_spot_2026_07_25.md`), and batch 1 itself
> archived alongside this plan.

## Todos

- [x] ✅ [REVIEW] P0. **DONE 2026-08-01.** The batch plan actually carries **11** todos, not 10 (todo 11 was added
      2026-07-26 same day, after this finalize plan's own todo text was drafted — noted, not itself a discrepancy in any
      evidence, just a stale count in this todo's own wording). All 11 re-verified against reality: **Ancestor checks**
      — `agent-orchestrator`: `361e0fe`/`d66fbf2`/`2530316`/`3e5de0e7b`/`867b1731e`/`7cd01e67c75` all confirmed
      ancestors of HEAD; `unified-trading-pm`: `dd172d6b7` confirmed ancestor; `deployment-ui@5663aa0` +
      `unified-trading-system-ui@369eea00` both confirmed ancestors. **Named test re-runs** — all PASS on a live re-run
      (not trusted from the claim): `tests/test_db_read_only_session.py` (2),
      `tests/test_regen_backlog_from_plan.py -k     circuit_breaker or aborts_before_any_prune` (3),
      `tests/test_git_health_dirty_consecutive_ticks_gate.py` (4, incl. the clean-blip case),
      `tests/test_dirty_state_resolution.py`+`tests/test_head_backward_canary.py` (48, incl. the new canary regression
      test), `tests/test_done_task_delete_trace.py` (4, new). **Real discrepancy found and fixed**: both
      `git_status_reporter_stale_public_url_token_expiry_2026_07_24.md` and
      `orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24.md` (plus this batch plan's own
      todo 3) cited `unified-trading-pm@421262a` as the loopback-preference fix — that sha is actually an unrelated
      `uts-backmerge-bot` merge commit touching only `workspace-manifest.json`; the real fix is
      `unified-trading-pm@804fa2b9a` (an ancestor of `421262a`, confirmed via `git merge-base --is-ancestor`). Fixed the
      citation in all 3 places; the underlying WORK itself was never in question (the loopback-preference logic was
      independently confirmed present and correct by reading the shipped script). **Environment limitation, not a
      regression signal**: `tests/test_slot_git_status_loopback_preference.bats` and
      `tests/test_slot_cron_ff_pull_dirty_gate.bats` could not be re-run — no `bats` binary is installed anywhere on
      this host (matches the pre-existing `pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md` finding);
      verified by reading the shipped script logic instead (the `_ORCH_URL_EXPLICIT`/loopback-probe code is present and
      matches the described behavior). `tests/smoke/wizard-stepper.spec.ts` (playwright) could not run — no Chromium
      browser binary installed (`npx playwright install` never run in this environment); verified by reading
      `tests/e2e/_shared/config.ts` instead (`NEXT_PORT = 3100 + SLOT` / `API_PORT = 8030 + SLOT` logic present and
      correct). Neither gap indicates the shipped fix regressed — both are pre-existing environment gaps, not new
      findings requiring a new todo.
- [x] ✅ [REVIEW] P0. **DONE 2026-08-01.** Reconciled each verified todo's evidence back into its TRUE source doc's own
      checkbox — **10 of the 11 named docs already had their checkbox correctly flipped at the time of the original
      fix** (the workers who did batch todos 1-5 flipped both the batch plan AND the true source doc in the same
      session, so "the source docs' own checkboxes are the ones that go stale" premise did not actually materialize for
      them): `orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md` (2×P1+P2 already `[x]`),
      `orchestrator_planregen_prune_wipes_backlog_on_transient_zero_derivation_2026_07_25.md` (2×P2 already `[x]`),
      `git_status_reporter_stale_public_url_token_expiry_2026_07_24.md` (already `[x]`, sha corrected above),
      `orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24.md` (already `[x]`, sha corrected
      above), `git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md` (both already `[x]`),
      `playwright_reuse_existing_server_cross_slot_false_results_2026_07_20.md` (already `[x]`),
      `dispatch_sequential_gate_fix_2026_07_24.md` (already `[x]`, self-serviced 2026-07-29),
      `gated_skip_park_no_slack_page_2026_07_25.md` (evidence added 2026-08-01 by this session's own batch-todo-8 work),
      `orphan_rootm_branch_unmerged_work_2026_06_05.md` (prose verdict already present, dated 2026-07-30), and
      `ao_backlog_done_row_disappearance_2026_07_25.md` (evidence added 2026-08-01 by this session's own batch-todo-10
      work). **One doc genuinely needed a fresh append**: `slot_double_reset_dataloss_race_2026_07_25.md`'s
      `[BACKEND] P3` was already `[x]` but had deferred its OWN verification to this batch plan without ever getting the
      actual evidence back — added a Progress Log entry citing `agent-orchestrator@7cd01e67c75`'s new canary regression
      test, closing that loop for real.
- [x] ✅ [INFRA] P0. **DONE 2026-08-01.** Every named entry re-checked against its actual current doc state (not trusted
      from the 2026-07-31 re-triage banner alone): - **Watchdog-cluster ordering decision**: CLEARED + shipped —
      `agent-orchestrator@64b5310` (soften) and `@77fc60a` (harden) both confirmed ancestors of HEAD. - **Failover
      release-signal** (`orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md` BACKEND P2): CLEARED — the
      ordering decision it was sequenced behind is ruled. Zero file-collision hits on `server/failover.py` (its one
      other corpus mention is an already-`[x]` "is this dead code" question). → **batch 2**. - **`/done`-semantics
      pair** (`reaper_kills_inflight_detached_quickmerge_false_done_2026_07_24.md` INFRA P1 + `orchestrator_failover...`
      BACKEND P3): the ORIGINAL gate (the operator-merge-gate governance question) IS cleared —
      `watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26.md`'s own 2026-07-31 Progress Log already says so.
      **But a NEW file-collision surfaced on re-check**: `server/routes/slots_worker.py` (both todos' target file)
      already carries 2 OTHER open todos from active docs —
      `cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29.md` `[BACKEND] P3` and
      `data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md` `[DATA]`/`[CODE]` P2 (both touch `_done_one_off`,
      the one-shot-completion neighbor of the regular `/done` handler). **STILL HELD — different reason now**
      (file-collision, not governance) — not batch-2 material until those land or a conflict-check clears it. -
      **AutoSpawn no-eligible-worker gap**
      (`orchestrator_ready_p1_task_undispatched_no_matching_worker_autospawn_gap_2026_07_25.md`): **MOOT, remove from
      Deferred** — this doc is `status: resolved`, all 3 todos already `[x]`, fully archived independent of batch-1. Not
      batch-2 material (already done). - **`_ahead_push` rejected-push item**
      (`ahead_push_sentinel_stale_after_amend_no_rejected_push_retry_2026_07_24.md` BACKEND P3): the test-module
      collision half of its gate is moot (the gate-aware sweep it would have collided with already shipped), but its OWN
      doc's real blocker — "(a) retry-on-new-HEAD vs (b) surface-as-visible-blocked, a genuine design decision on the
      single riskiest automated code path in the system" — is UNCHANGED and unresolved. **STILL HELD**, needs operator
      sign-off on (a)/(b), not batch-2 material. - **Periodic dirty-resolution sweep**
      (`idle_slot_dirty_wip_never_auto_resolves_2026_07_20.md` BACKEND P2 ×2): CLEARED — the operator-merge-gate bypass
      its own gate cited is resolved (same `@49c919d`). Zero file-collision hits on
      `server/worktree_clean_check/_orphan.py`/`commit_and_push_dirty_repos`. → **batch 2**. - **Regen
      positional-task-id deferral**: unchanged — already RULED 2026-07-28, dispatch directly from
      `regen_positional_task_ids_not_content_stable_2026_07_17.md`, not batch material (per the original text). -
      **`slack-read-channel.py` env-var compliance**: unchanged — already cleared per the ratchet measurement, dispatch
      directly from `plan_health_tests_leak_real_slack_alerts_2026_07_24.md`, not batch material. - **Two QG-harness
      worktree-isolation items** (`utl_shared_clone_commits_repeatedly_reset_2026_07_22.md` items 4/5): unchanged —
      still too high blast-radius (changes what "QG green" means), still needs its own scoped plan with operator
      sign-off. - **Bonus finds beyond the named list, surfaced by the same re-check discipline**: (1)
      `orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24.md` (in the OTHER Deferred section,
      "operator decision needed") is fully `status: resolved`, all 4 todos `[x]` (done 2026-07-30, independent of the
      noted "no longer operator-gated, pick it up" text) — **MOOT, remove from Deferred**. (2)
      `escalation_backlog_repo_collision_blind_spot_2026_07_25.md`'s OPERATOR-DECISION was already resolved+shipped
      (`agent-orchestrator@7c937f99e0`) but never flipped — fixed earlier in this same pass (see todo 2's evidence
      above, and its own doc). (3) `reaper_kills...`'s slot-8/slot-9 commit-recovery item already carries an accurate
      2026-07-31 "very likely MOOT" finding in its own Progress Log (the plans it blocked are archived) — confirmed
      current, no new action needed. (4) The watchdog cluster's OTHER satellite docs
      (`killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md`'s reclaim-and-push todo,
      `host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26.md`'s admission-gate todo,
      `one_shot_worker_completes_but_no_clean_exit_signal_watchdog_rekicks_2026_07_25.md`'s residual-risk todo,
      `wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md`'s 3 todos) each have their OWN ordering
      gate cleared now too, but were NOT individually file-collision-checked in this pass (out of this todo's
      explicitly-named scope) — recommend a fresh `/ag-closeout-audit ao` or manual conflict-check pass before drafting
      them into a plan, rather than rushing under-checked work in. **2 items spun into batch 2** (see
      `ao_satellite_ao_dispatch_batch2_2026_08_01.md`); the rest recorded above with their current, specific reason.
- [x] ✅ [REVIEW] P0. **DONE 2026-08-01.** The 3 originally-named docs
      (`ao_repo_docs_deleted_against_instructions_dead_code_refs_2026_07_23.md`,
      `orchestrator_slots_context_directive_issued_missing_migration_2026_07_25.md`,
      `slot_double_reset_dataloss_race_2026_07_25.md`) were ALREADY archived + repointed in
      `/plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md`'s own Track table (verified — all 3 links already
      resolve to `/plans/archive/issues/...`, no stale paths found). **One NEW doc found + archived this pass**:
      `escalation_backlog_repo_collision_blind_spot_2026_07_25.md` (surfaced during todo 3's Deferred re-check — its
      OPERATOR-DECISION was resolved+shipped 2026-07-31 but never archived). Ran the 6-step ritual: `> 🟢 ARCHIVED`
      banner added, `git mv` to `plans/archive/issues/`, 3 genuine path-style referrers fixed
      (`ao_consolidated_closeout_2026_07_25.md`'s Track link,
      `ao_dispatch_priority_inversion_starvation_has_no_page_path_2026_07_30.md`'s `related:` entry, this batch's own
      Deferred-section prose), and the stale "operator-gated" table row in
      `ao_open_issues_consolidated_close_out_2026_07_17.md` corrected (12→10, both this doc and
      `idle_slot_dirty_wip_never_auto_resolves_2026_07_20` struck through with their resolution).
      `grep -rn     "/plans/active/issues/escalation_backlog..."` now returns zero hits — only bare-filename prose
      mentions remain (expected, not path links). **`run_hygiene_sweep.sh --ci` does NOT report zero hard failures
      corpus-wide** — 5 hard failures found, but every one verified NOT caused by this pass: `check_archive_candidates`
      (22 vs baseline 4) and `check_terminal_status_archived` (12 vs baseline 1) list 22/12 docs across
      cefi/defi/tradfi/prediction/ mtds/mdps/github_actions — NONE touched by batch 1 or this finalize pass, and this
      exact ratchet backlog is already tracked in `plan_reconcile_autonomous_sweep_2026_07_30.md` (baseline was 7 as of
      2026-07-30, so this is pre-existing multi-tranche drift, not new); `check_reference_paths` (191 vs 161 format, 889
      vs 901 existence — existence actually IMPROVED) lists only `codex/15-runbooks/`/`codex/16-strategy-playbooks/`
      files never touched here, already tracked in `reference_path_convention_2026_07_23.md`;
      `check_ag_closeout_linkage` (77 vs baseline 69) — confirmed neither batch1, this finalize plan, nor the new batch2
      plan appear anywhere in its orphan list. `check_todo_regression` flags THIS finalize plan itself (origin=6,
      current=5) — a verified, deliberate fix: an earlier edit this same pass accidentally left a duplicate stale copy
      of todo 2's text (both the flipped `[x]` version and the original `[ ]` text existed at once); removing the
      duplicate correctly drops the count from a buggy 6 to the true 5. Zero net regression. Full detail of all 5
      verified-unrelated failures in this doc's own shell history; not re-litigated here.
- [x] ✅ [INFRA] P0. **DONE 2026-08-01.** Every remaining Deferred item confirmed already tracked as a `- [ ]` todo in
      its own source doc (none existed only as batch-1 prose) — no migration needed beyond the 2 items already spun into
      batch 2 in todo 3. `> 🟢 ARCHIVED` banner added to
      `/plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_2026_07_26.md` (status frontmatter also flipped
      `active`→`complete`, and its own stale in-body "status: draft" banner — a leftover from authoring, never updated
      when the plan was flipped active — corrected in the same edit). `git mv`'d to `plans/archive/2026_07/`. All 17
      genuine absolute-path referrers across the corpus fixed (bulk `sed`, verified zero remaining
      `/plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26` hits) — including this finalize plan's own `related:`
      entry (its `depends_on:` correctly stayed a bare slug per convention, untouched).
      `regenerate_active_plan_inventory.py` does not exist as a standalone script (stale reference in this todo's own
      text) — the inventory regen is already part of `run_hygiene_sweep.sh`, re-run post-archival: **0 orphans** (down
      from 2 pre-archival), 243 plans (was 244). `check_finalize_plan_coverage.py` — **0 violations, exit 0**, no longer
      names this pair (confirmed via direct grep on its output — batch1's `assigned_vm: NA` puts it outside that check's
      scope entirely, and this finalize plan is `status: active`, not stuck-at-draft). **This finalize plan itself then
      reached 5/5 `[x]`, `locked_by:` empty — archived immediately in the same pass** (per the workspace's own
      archive-immediately rule), with the same 6-step ritual (banner, `status: active`→`complete`, `git mv`, 7 more
      corpus referrers fixed). Final re-run of `run_hygiene_sweep.sh`: **0 orphans, 242 plans**, and the
      `check_todo_regression` false-positive this pass caused is now fully gone too (archiving took this doc out of the
      active-plans-vs-origin diff scope entirely) — down to the 4 pre-existing, verified-unrelated hard failures
      documented above.

## Codex SSOTs

`/codex/11-project-management/` (findings triage + the archival ritual),
`/codex/11-project-management/cross-reference-path-convention.md` (the corpus-wide referrer fixup),
`/codex/12-agent-workflow/commit-push-flip-rule.md` (evidence-backed flips),
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility".

## Progress Log

- **2026-07-26** — Authored in the same turn as its batch by `/ag-closeout-audit ao` (autonomous mode).
  `sequential: true` is deliberate here: the five todos are a genuine chain (verify → reconcile → re-check gates →
  archive sources → archive self) and several touch the same files. Left `status: draft`.
