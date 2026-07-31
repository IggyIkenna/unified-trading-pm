---
doc_type: plan
title: CI satellite AO batch 2 — finalize (reconcile source docs, re-check deferrals, archive)
summary: >-
  Gated closeout for ci_satellite_ao_dispatch_batch2_2026_07_29.md — machine-held via depends_on + gate_on_depends: true
  until all 14 of that plan's todos are done. Reconciles each distinct source doc's checkboxes/prose independently,
  re-checks the file-contention Deferred items (E1-E5) for whether the file they were rationed away from is free again,
  re-verifies the operator-gated/role-mismatch/too-large items (E6-E14) for any state change, and archives batch 2 via
  the standard 6-step ritual.
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci, cicd, ao-dispatch, close-out, batch-2, satellite-docs, archival]
related:
  [
    /plans/active/ci_satellite_ao_dispatch_batch2_2026_07_29.md,
    /plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: "2026-07-29"
last_updated: "2026-07-30"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.6
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ci_satellite_ao_dispatch_batch2_2026_07_29]
gate_on_depends: true
source: >-
  `/ag-closeout-audit ci` run 2026-07-29, per `plans/active/task_template.md` §4's finalize-plan-coverage rule — every
  AO-dispatched plan needs a companion gated finalize plan, mirroring the batch1 precedent.
assigned_role: cicd
sequential: true
drift_direction: advance-code
---

# CI satellite AO batch 2 — finalize

> **🟢 STATUS: `active` — dispatched.** Drafted 2026-07-29 as part of a scheduled autonomous `/ag-closeout-audit ci`
> run; flipped active alongside the batch it gates once all 14 of that plan's todos completed (2026-07-31). Stale banner
> corrected 2026-07-31 (this doc-flip commit) — the frontmatter has read `status: active` since the gate cleared; the
> body text simply never caught up until now.

> **Machine-gated on `ci_satellite_ao_dispatch_batch2_2026_07_29.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue anything below until all 14 of that plan's todos are `done`. `sequential: true` because todo
> 1 must land before todo 2's reconciliation cites it, todo 3 needs both, and todo 4 (archival) must run last.

## Todos

- [x] ✅ [REVIEW] P1. **Reconcile all 14 batch-2 todos' source docs.** Each batch-2 todo ends with `Source:` naming one
      or more docs (todo 1 cites two, todo 6 cites one 7-todo doc, several cite a single doc's multiple items). For
      each: flip the corresponding checkbox or annotate the corresponding prose section in EVERY cited doc, citing the
      batch-2 commit that shipped it — **verify the cited commit exists and is an ancestor of `origin/live-defi-rollout`
      before citing it** (`git merge-base --is-ancestor`). Then, per doc, re-check whether it now has zero open work
      **in checkbox AND prose form**. Only set `status: resolved` on a doc that genuinely reaches zero. **Done when**:
      every cited doc is flipped/annotated with verified evidence, and each doc that genuinely reaches zero open work is
      `status: resolved`. **DONE 2026-07-31 (slot 6, review craft).** Enumerated all 14 batch-2 todos' `Source:`
      citations → 9 distinct docs: `qg_sentinel_environment_blind_2026_07_23.md` (todos 1/2/3),
      `ci_test_content_and_tooling_speed_findings_2026_07_28.md` (todos 1/7/8/9),
      `promotion_lag_alert_hides_provenance_block_2026_07_17.md` (todo 4),
      `check_strict_quickmerge_blind_to_dirty_deps_carveout_2026_07_23.md` (todo 5),
      `breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md` (todo 6),
      `mtds_ungated_test_families_2026_07_17.md` (todos 10/11),
      `qg_hardcoded_tmp_paths_false_failures_on_full_tmpfs_2026_07_26.md` (todo 12),
      `plan_health_agent_dead_schedule_trigger_2026_07_27.md` (todo 13), `monitoring_control_plane_master_2026_06_10.md`
      (todo 14). Verified all cited SHAs
      (`4545df4c6`/`3ed0fc99d`/`51b93ec0a`/`bbe9a9871`/`5607023a2`/`481e72d6f`/`f2f227ff9`, this repo) are ancestors of
      `origin/live-defi-rollout` via `git merge-base --is-ancestor`. 8 of 9 docs were **already** correctly
      flipped/archived by prior sessions (`qg_sentinel_environment_blind` and `breaking_change_differ_...` both
      genuinely stay `status: open` — each has one real remaining item outside batch-2's scope, correctly not
      force-closed; `ci_test_content_...`/`promotion_lag_alert_...`/`check_strict_quickmerge_...`/
      `mtds_ungated_test_families_...`/`qg_hardcoded_tmp_paths_...` all already `status: resolved`, 0 open checkboxes,
      already archived; `monitoring_control_plane_master` correctly stays `status: active` — G3 closed-with-citation, 3
      other genuinely-unrelated open items remain, deferred as batch2's own E13/E14). **1 gap found + fixed**:
      `plan_health_agent_dead_schedule_trigger_2026_07_27.md` was `status: resolved` with 0 open todos but had never
      been archived — moved to `/plans/archive/issues/`, added the standard ARCHIVED banner, and repointed both corpus
      referrers (`ci_satellite_ao_dispatch_batch2_2026_07_29.md` todo 13's own citation, and
      `ci_satellite_ao_dispatch_batch4_2026_07_31.md`'s archival-readiness table) to the new path — unified-trading-pm
      (this doc-flip commit).
- [x] ✅ [REVIEW] P1. **Re-check the 5 file-contention Deferred items (E1-E5) and re-verify E9-E10 (still-open F4
      items).** Each names the specific file/blocker it collided with, so this is a few greps and reads, not fresh
      investigation. In particular: is `scripts/quality-gates-base/base-service.sh` free again (batch-2 todo 1 landed)?
      If so, E1 (`pm_bats_tests`' BATS phase) and the `--durations=25`/`base-library.sh` half of E2 are both unblocked
      as FILES — note each as ready-for-batch-3 extraction. Is `scripts/quickmerge.sh` free again? If so, E3 (STAGE 1.6
      dormancy gate) and E4 (delete redundant pre-push hook) are both unblocked as FILES, in that priority order (E4 is
      P3/fully conflict-cleared already — E3 is P2 with an operator-confirmed ruling behind it; note the file contention
      between them for batch-3's own conflict-check to resolve). For E9/E10 (F4 crons/digest-drift-sweep): has the
      operator ruled since 2026-07-29? **Do NOT draft the follow-up todos here** — this plan's scope is reconciliation,
      not fresh drafting; note each as ready-for-batch-3 instead. Do NOT re-ask an operator question that was already
      escalated (E6, E8, E14); just record whether it has been answered. **Done when**: each of E1-E5, E9, E10 has
      either (a) a note that it is ready for batch-3 extraction because its file/blocker cleared, or (b) a re-verified
      confirmation the contention/gate is still open. **DONE 2026-07-31 (slot 3, review craft).** Confirmed batch-2 todo
      1 ([x]) and todo 11 ([x], line 386, the `${TMPDIR:-/tmp}` port) both landed, so all 3 contended files are free:
      **(a) E1** ready for batch-3 — `base-service.sh` free. **(a) E2** ready for batch-3 — `base-library.sh` free (todo
      11); note the `base-service.sh` half of this same source item was ALREADY shipped via todo 1(c) (`--durations=25`,
      confirmed 2026-07-30), so only the `base-library.sh` add remains to extract. **(a) E3** ready for batch-3 —
      `quickmerge.sh` free, P2, operator-ruled. **(a) E4** ready for batch-3 — `quickmerge.sh` free, P3, fully
      conflict-cleared, top of the batch-3 queue for this file. **Mixed: E5** — file contention on `quickmerge.sh` is
      cleared, but its own internal step-2 precondition is NOT: re-read
      `quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md` directly — its "Suggested next steps" #2
      (`UnifiedCloudServicesConfig.environment`'s alias-precedence caller audit, the real root cause) and its own
      `## Todos` entry (steps 2-4 bundled) are both still `- [ ]` unstarted; step 3 (the quickmerge.sh branch-check
      broadening) is explicitly gated on step 2 by that doc's own text, independent of file availability. So E5 is
      file-clear but blocker-still-open — batch-3 cannot dispatch step 3 alone; step 2 (the alias-precedence fix +
      caller audit, NOT a quickmerge.sh touch) is the actual next actionable unit. **(b) E9** still open — searched for
      any operator ruling since 2026-07-29 on the `digest-drift-sweep` non-convergence: found none. The only ruling on
      record (`autonomous_session_operator_decisions_2026_07_25.md` item #28, dated 2026-07-26, "resolved — option A")
      predates E9's creation and is already fully incorporated into its framing (that ruling only scoped the
      hardening-fix todo, explicitly deferring the non-convergence root cause — which is exactly what E9 tracks). The
      underlying `[INFRA] P2` todo in `post_cutover_silent_assumption_sweep_2026_07_23.md` (line 541) remains `- [ ]`
      unchecked. **(b) E10** still open — same search, same result: no per-cron disable-vs-fix ruling found;
      `na-eligibility-audit 2026-07-30` reconfirmed E10 stays parked as-is ("The F4 vacuous-cron item is parked as ci
      batch2 Deferred E10"). No code shipped (pure reconciliation read); Evidence: `unified-trading-pm@<pending-sha>`.
- [ ] [REVIEW] P2. **Re-verify E7 and E11-E13 have not silently changed state.** E7 (MTDS DEPLOYMENT_ENV leak,
      duplicate-gated on the sibling race doc's cascade-instrumentation step) — has that sibling doc's blocking step run
      yet? E11 (dirty-deps carve-out sibling docs) — still out of batch-2 todo 5's narrow scope, confirm no new doc has
      claimed them. E12/E13 (role-mismatch, UI-touching) — still waiting on a `[UI]`-capable slot cycle; no action
      needed here beyond confirming they have not been separately picked up. **Done when**: each is re-confirmed still
      in its recorded state, or flagged if changed.
- [ ] [DOC] P1. **Archive `ci_satellite_ao_dispatch_batch2_2026_07_29.md`** via the standard 6-step ritual (CLAUDE.md §
      plan archival): migrate any still-unresolved Deferred item to a tracked follow-up (todos 2-3 above should have
      resolved or re-confirmed E1-E14 — verify none silently vanishes) → add the archive banner → run the
      codex-alignment check (todo 1 above changed `/codex/08-workflows/ci-cd-flow.md` — confirm that landing is
      reflected and no NEW durable contract is undocumented, e.g. the QG sentinel's configuration-binding behavior, the
      new PYTEST_UNIT_DIR fleet-sweep checker) → update CLAUDE.md/codex if any batch-2 todo established a new contract →
      grep the corpus for every referrer of `ci_satellite_ao_dispatch_batch2_2026_07_29` and repoint each to the
      archived path → clear `locked_by` (already empty; confirm). **Done when**: the plan is in
      `plans/archive/2026_07/`, every corpus referrer resolves, `check_reference_paths.py` has not regressed, and this
      finalize doc is archived alongside it in the same commit.

## Codex SSOTs

- `/codex/06-coding-standards/quality-gates.md` — how the gate composes; ratchet-baseline convention
- `/codex/08-workflows/ci-cd-flow.md` — the pipeline contract batch-2 todo 1/2 touch
- `/codex/11-project-management/` — archival ritual, issue-doc lifecycle
- `plans/active/task_template.md` §4 — the finalize-plan-coverage rule this plan satisfies

## Progress Log

- **2026-07-29** — Drafted alongside `ci_satellite_ao_dispatch_batch2_2026_07_29.md` by `/ag-closeout-audit ci`
  (autonomous mode, `ag_closeout_auditor` scheduled worker, slot 7). Both are `status: draft`; neither is dispatched.

- **2026-07-31 (slot 6, review craft)** — dispatched todo 1 (gate cleared: all 14 batch-2 todos done). Reconciled all 9
  distinct source docs the 14 todos cite; found + fixed 1 gap (`plan_health_agent_dead_schedule_trigger_2026_07_27.md`
  was resolved but never archived — archived it + fixed both corpus referrers). Also corrected this plan's own stale
  `draft`-status banner (frontmatter has read `active` since the gate cleared 2026-07-31, body text hadn't caught up).
  See todo 1's own inline evidence for the full per-doc breakdown. Todo 2 (Deferred-item re-check) is next in the
  `sequential: true` chain.

- **2026-07-31 (slot 3, review craft)** — dispatched todo 2 (all 3 contended files confirmed free: batch-2 todos 1 and
  11 both landed). Re-checked all 7 items: E1-E4 all ready-for-batch-3-extraction (files clear); E5 file-clear but its
  own internal step-2 precondition (a separate alias-precedence fix, not a file-contention issue) is still unstarted, so
  it is NOT simply ready — flagged as mixed rather than force-marked ready; E9/E10 both re-confirmed still open, no
  operator ruling found since 2026-07-29. See todo 2's own inline evidence for full citations. Todo 3 (E7/E11-E13
  re-verify) is next in the `sequential: true` chain.
