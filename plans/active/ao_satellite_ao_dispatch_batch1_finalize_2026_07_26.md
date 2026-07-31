---
doc_type: plan
title: AO satellite AO batch 1 — finalize
summary: >-
  Gated closeout for ao_satellite_ao_dispatch_batch1_2026_07_26.md — machine-held via depends_on + gate_on_depends until
  every todo in that batch is done. Reconciles each completed todo's evidence back into its TRUE source issue doc (the
  batch was an extraction, so the source docs' own checkboxes are the ones that go stale), re-checks whether any
  Deferred item's gate has since cleared, archives the source docs that reach zero open todos, and runs the standard
  6-step archival ritual on the batch plan itself.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-1, finalize]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md,
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

> **Machine-gated on `/plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md`** (`depends_on` +
> `gate_on_depends: true`) — was undispatched until every todo in that batch was `done`. **Gate cleared 2026-08-01**:
> the batch reached 11/11 `[x]`, `locked_by:` empty. Reassigned to `assigned_vm: NA` / `execution_scope: local-only`
> (operator instruction, 2026-08-01) so this finalize pass runs interactively rather than waiting on AO dispatch.

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
- [ ] [REVIEW] P0. **Reconcile each verified todo's evidence back into its TRUE source doc's own checkbox** — batch 1
      was an extraction, so the 13 source-doc todos it covers are the ones that go stale, not the batch's. Flip the
      specific todo in each of: `orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md` (3 todos — 2×P1 + the
      P2 timeout alignment), `orchestrator_planregen_prune_wipes_backlog_on_transient_zero_derivation_2026_07_25.md`
      (2×P2), `git_status_reporter_stale_public_url_token_expiry_2026_07_24.md` (INFRA P2) AND
      `orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24.md` (SCRIPT P2) — **both**, since
      batch todo 3 folded a genuine duplicate pair — `git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md`
      (2×INFRA P2), `playwright_reuse_existing_server_cross_slot_false_results_2026_07_20.md`,
      `dispatch_sequential_gate_fix_2026_07_24.md` (BACKEND P1 only), `slot_double_reset_dataloss_race_2026_07_25.md`,
      `gated_skip_park_no_slack_page_2026_07_25.md`, `orphan_rootm_branch_unmerged_work_2026_06_05.md` (a prose doc with
      NO checkbox surface — add a dated verdict section instead of a flip), and
      `ao_backlog_done_row_disappearance_2026_07_25.md` (BACKEND P3 only). **Done when**: every one of those flips or
      verdict sections is committed with the `docs(plans):` prefix and cites the real commit sha.
- [ ] [INFRA] P0. **Re-check every Deferred item's gate and spin the cleared ones into batch 2** — walk both Deferred
      sections of the batch plan and, for each entry, state whether its named gate has cleared: the watchdog-cluster
      ordering decision, the failover release-signal item (gated on that ordering), the `/done`-semantics pair (gated on
      the operator-merge-gate decision in `watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26.md`), the
      AutoSpawn gap (file-collision-gated on batch todo 1, which by this point HAS landed — so this one should clear),
      the `_ahead_push` rejected-push item, the periodic dirty-resolution sweep, the regen positional-task-id deferral,
      the `slack-read-channel.py` env-var compliance question, and the two QG-harness worktree-isolation items. **Done
      when**: each entry is marked cleared-and-moved (naming the new batch-2 plan and todo) or still-gated with the
      current reason — no entry left unstated.
- [ ] [REVIEW] P0. **Archive every source doc that has reached zero open todos, and repoint the AO closeout's Sources**
      — run the standard 6-step archival ritual per doc (migrate any DEFERRED item into a tracked todo → add the
      `> **🟢 ARCHIVED**` banner → codex-alignment check → update CLAUDE.md/codex if a contract changed → fix every
      referrer's path corpus-wide → clear the lock). At minimum this covers the two docs that were ALREADY fully done
      before batch 1 ran (`ao_repo_docs_deleted_against_instructions_dead_code_refs_2026_07_23.md` and
      `orchestrator_slots_context_directive_issued_missing_migration_2026_07_25.md`) plus any source doc batch 1 emptied
      (`slot_double_reset_dataloss_race_2026_07_25.md` is the likeliest). **Every one of these is cited as a Source in
      `/plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md`** (archived 2026-07-30 by
      `ao_consolidated_closeout_2026_07_25_finalize_2026_07_30.md`'s own todo — its 2 `## Todos` items were done and it
      carried zero others; archiving the digest itself does not close the tranche), **so the same commit MUST repoint
      that doc's Track entries at `plans/archive/`** or the tranche reference is silently orphaned. **Done when**:
      `grep -rl <slug> plans/ codex/` returns only the archived copy's own path for each archived doc, the AO closeout's
      Sources resolve, and `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports zero hard failures.
- [ ] [INFRA] P0. **Run the 6-step archival ritual on the batch plan itself, then regenerate the inventory** — banner
      `/plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md`, migrate any still-Deferred item into batch 2 (never
      leave a deferral that is not already a `- [ ]` todo somewhere), move the file to `plans/archive/2026_07/`, fix
      every corpus-wide referrer including this finalize plan's own `related:`/`depends_on:`, then run
      `.venv/bin/python scripts/plan-hygiene/regenerate_active_plan_inventory.py`. **Done when**: the batch plan is
      archived with a banner, the inventory regenerates with an orphan count of 0, and `check_finalize_plan_coverage.py`
      no longer names this pair.

## Codex SSOTs

`/codex/11-project-management/` (findings triage + the archival ritual),
`/codex/11-project-management/cross-reference-path-convention.md` (the corpus-wide referrer fixup),
`/codex/12-agent-workflow/commit-push-flip-rule.md` (evidence-backed flips),
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility".

## Progress Log

- **2026-07-26** — Authored in the same turn as its batch by `/ag-closeout-audit ao` (autonomous mode).
  `sequential: true` is deliberate here: the five todos are a genuine chain (verify → reconcile → re-check gates →
  archive sources → archive self) and several touch the same files. Left `status: draft`.
