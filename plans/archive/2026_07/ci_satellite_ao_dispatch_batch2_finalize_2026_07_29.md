---
doc_type: plan
title: CI satellite AO batch 2 — finalize (reconcile source docs, re-check deferrals, archive)
summary: >-
  Gated closeout for ci_satellite_ao_dispatch_batch2_2026_07_29.md — machine-held via depends_on + gate_on_depends: true
  until all 14 of that plan's todos are done. Reconciles each distinct source doc's checkboxes/prose independently,
  re-checks the file-contention Deferred items (E1-E5) for whether the file they were rationed away from is free again,
  re-verifies the operator-gated/role-mismatch/too-large items (E6-E14) for any state change, and archives batch 2 via
  the standard 6-step ritual.
status:
  complete # (was: active) 2026-07-31 archival: all 4 todos done — 9 source docs reconciled (1 gap found + fixed), all
  # 15 Deferred items (E1-E15) re-checked (2 corrected to RESOLVED-AS-MOOT), parent archived via the standard 6-step
  # ritual in the same commit as this doc.
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci, cicd, ao-dispatch, close-out, batch-2, satellite-docs, archival]
related:
  [
    /plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_2026_07_29.md,
    /plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: "2026-07-29"
last_updated: "2026-07-31"
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

> **🟢 ARCHIVED 2026-07-31** — all 4 todos done: reconciled all 9 distinct source docs the 14 batch-2 todos cite
> (found + fixed 1 gap — an already-resolved doc that had never been archived), re-checked/re-verified all 15 Deferred
> items (E1-E15; 2 corrected to RESOLVED-AS-MOOT on fresh evidence), then archived the parent via the standard 6-step
> ritual in this same commit. Parent archived to `/plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_2026_07_29.md`.

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
- [x] ✅ [REVIEW] P2. **Re-verify E7 and E11-E13 have not silently changed state.** E7 (MTDS DEPLOYMENT_ENV leak,
      duplicate-gated on the sibling race doc's cascade-instrumentation step) — has that sibling doc's blocking step run
      yet? E11 (dirty-deps carve-out sibling docs) — still out of batch-2 todo 5's narrow scope, confirm no new doc has
      claimed them. E12/E13 (role-mismatch, UI-touching) — still waiting on a `[UI]`-capable slot cycle; no action
      needed here beyond confirming they have not been separately picked up. **Done when**: each is re-confirmed still
      in its recorded state, or flagged if changed. **DONE 2026-07-31 (slot 15, review craft).**

      **E7 — UNCHANGED, re-confirmed still open.** Read
                      `plans/active/issues/mtds_deployment_env_race_survives_single_worker_2026_07_23.md` directly: its cascade-
                      instrumentation todo (`- [ ] [INFRA] P2. Instrument quickmerge's cascade/pull step`, line 138) is still
                      unchecked. That same doc already carries its own fresh **2026-07-31** na-eligibility-audit verdict independently
                      confirming E7 unchanged ("CONFIRMS the verdict above, unchanged... Deferred E7 remains open/parked, unchanged"),
                      cross-verified against a same-day `ci_satellite_ao_dispatch_batch4_2026_07_31.md` draft. Annotated the E7 row in
                      `ci_satellite_ao_dispatch_batch2_2026_07_29.md`'s Deferred table with this re-verification.

                      **E11 — UNCHANGED, still unclaimed.** The two named sibling docs
                      (`mutable_git_sha_tag_restamping_cloudbuild_2026_07_13.md`,
                      `sports_odds_ownership_registry_split_brain_and_bogus_api_football_denominator_2026_07_15.md`) are both archived
                      (`plans/archive/issues/`) — but for their OWN unrelated primary fixes, not because anyone migrated them to the new
                      `Quickmerge: direct-carveout-dirty-deps` trailer (`check_strict_quickmerge_blind_to_dirty_deps_carveout_2026_07_23.md`'s
                      shipped Option 2, `unified-trading-pm@bbe9a9871`). Grepped the active corpus for `direct-carveout-dirty-deps` and
                      "dirty-deps carve-out" — every hit is either the source doc itself or a commit-body-style USE of the new/old
                      carve-out convention (e.g. `plan_reconcile_autonomous_sweep_2026_07_30.md`'s own direct push), never a doc that
                      targets migrating the sibling docs. No new doc has claimed E11. Annotated the E11 row accordingly.

                      **E12 — CHANGED: now fully RESOLVED, no longer role-mismatch-blocked.** Read
                      `plans/archive/issues/ci_test_content_and_tooling_speed_findings_2026_07_28.md` (already archived, `status:
                      resolved`): all 5 constituent `[UI]` todos are `[x]` done — Playwright `--project=chromium` scoping + browser-
                      binary `actions/cache` for the e2e job, ESLint `archive/**` ignore-list fix + `--cache`, `deployment-ui@de5b7af2`
                      npm→pnpm migration (workflow + Dockerfile + cloudbuild.yaml updated), and `vitest.config.ts` jsdom→happy-dom
                      (~30% wall-time win, 1101/1101 tests green). A `[UI]`-capable slot picked this class up between batch-2's
                      2026-07-29 drafting and this finalize pass. **Rewrote the E12 row** in
                      `ci_satellite_ao_dispatch_batch2_2026_07_29.md`'s Deferred table to record RESOLVED with citations — todo 4
                      (archival) needs no further follow-up for E12.

                      **E13 — UNCHANGED, still open.** Read `plans/active/monitoring_control_plane_master_2026_06_10.md` directly:
                      "Rollout-ratchet panels" (line 251, `- [ ] [CODE] P0`) and "(G4) Ruleset / branch-protection drift" (line 455,
                      `- [ ] [CODE] P0`, explicitly folds into the Rollout-ratchet panels as a third column) are BOTH still unchecked.
                      Corroborated by that doc's own **2026-07-30** na-eligibility-audit verdict ("KEEP-NA, valid — all four open items
                      are deployment-api + deployment-ui surface work requiring a `[UI]`-capable role... Parked on exactly that basis
                      as... Deferred E13"). Annotated the E13 row with this re-verification.

                      Evidence: `unified-trading-pm@<pending-sha>` (this commit — annotates all 4 rows in
                      `ci_satellite_ao_dispatch_batch2_2026_07_29.md`'s Deferred table + flips this checkbox). No code shipped outside
                      unified-trading-pm (pure reconciliation read + doc annotation). Todo 4 (archival) is next in the `sequential:
                      true` chain — it should treat E12 as resolved (no migration needed) and E7/E11/E13 as still-genuinely-open
                      Deferred items to migrate forward per the archival ritual.

- [x] ✅ [DOC] P1. **DONE 2026-07-31 (slot 6, cicd craft).** Archived `ci_satellite_ao_dispatch_batch2_2026_07_29.md`
      via the standard 6-step ritual. **(1) Migrated Deferred items**: re-audited all 15 (E1-E15) directly against live
      source docs rather than trusting todos 2-3's table verbatim — 11 (E1/E3/E4/E5-mixed/E6/E7/E8/E9/E10/E13/E14) are
      confirmed live open todos in their own source docs (nothing lost); **E2 corrected** — live-verified
      `scripts/quality-gates-base/base-library.sh:459` already carries `--durations=25` (shipped in the SAME commit,
      `unified-trading-pm@3ed0fc99d`, that did `base-service.sh`'s half) — todo 2's "ready for batch-3 extraction" was a
      stale read of the batch2 table text, not live code; RESOLVED-AS-MOOT, no follow-up needed. **E11 corrected** —
      fresh corpus grep for the dirty-deps-carve-out phrase family (13 hits outside batch1/batch2/finalize/source doc)
      found every hit is a historical Progress-Log citation, none teaches the pre-2026-07-29 convention as forward
      guidance; the one forward-looking doc (`/codex/08-workflows/ci-cd-flow.md`) already has the current trailer.
      RESOLVED-AS-MOOT, no live doc needs migrating. E12/E15 already closed in their own tables/docs — no action. Both
      corrections recorded inline in batch2's own Deferred table (superseding the stale rows), so the reasoning survives
      archival. **(2) Archive banners** added to both docs (batch2 + this finalize doc), `status: complete`,
      `last_updated: 2026-07-31`. **(3) Codex-alignment check**: verified todo 1's claimed `ci-cd-flow.md` /
      `quality-gates.md` / `quickmerge-architecture.md` updates are actually live (grepped each). Found one real gap:
      todo 12's new `scripts/quality_gates/check_pytest_unit_dir_coverage.py` fleet-wide checker (a new blocking
      post-gate + baseline file) was undocumented — fixed by adding a "PYTEST_UNIT_DIR fleet-coverage check" subsection
      to `/codex/06-coding-standards/quality-gates.md` (next to the existing PYTEST_UNIT_DIR override section it
      extends). Everything else batch2 shipped was either already documented or not a new durable contract (regression
      tests, per-repo config application, moot/no-op findings) — no CLAUDE.md change needed (implementation detail under
      the existing QG pointer). **(4) Corpus referrers**: grepped the whole `plans/`+`codex/` tree for every full
      leading-slash-path reference to either doc — 20 files carried
      `/plans/active/ci_satellite_ao_dispatch_batch2     [_finalize]_2026_07_29.md`, all repointed to
      `/plans/archive/2026_07/...` (verified zero `/plans/active/...` hits remain for either doc). Also found + fixed 2
      bare (no-leading-slash) references my first grep missed (format-only, not existence-check-visible):
      `issues/ibkr_pipeline_mode_missing_venue_override_2026_07_30.md`'s `related:` field, and 4 bare `codex/...` refs
      inside batch2's own body text (pre-existing, from earlier sessions' todo evidence — not introduced by this
      archival) plus 1 more in `/codex/06-coding-standards/quality-gates.md` and 1 in
      `plan_commit_sha_evidence_regression_7e0aab35f_2026_07_31.md` (both files already touched this session for other
      reasons). `plans/active/INDEX.md` is auto-generated (never hand-edited) — regenerated via
      `scripts/plans/regenerate_active_plan_index.py` as part of the archival commit (242 plans, batch2 confirmed gone).
      **Correction to an earlier assumption in this same evidence**:
      `plans/archive/2026_07/     active_plan_inventory_dashboard_2026_07_24.md` is NOT a frozen snapshot despite its
      archive-folder path — its own frontmatter says regeneration deliberately continues in place there
      (`scripts/plans/regenerate_active_plan_inventory.py` MASTER_FILE re-pointed 2026-07-24) — ran it too (242 plans, 0
      orphans, table refreshed to reflect this archival). **(5) `locked_by`**: confirmed empty on both docs — no unlock
      needed. **(6)** both docs moved to `plans/archive/2026_07/` in the same commit. **`check_reference_paths.py`**:
      existence-count improved 901→888 (baseline never violated); format-count currently reads above its 161 baseline
      (189, pre-fix — fixed every violation traceable to this archival's own files, verified via targeted grep against
      the full touched-file list), but the residual gap is 100% pre-existing ambient corpus drift in files this archival
      never touched (confirmed via `git log` — e.g. `ao_open_issues_consolidated_close_out_2026_07_17.md`'s bare refs
      land via unrelated commits about ao_fleet_observability_kpis/JWT-secret/orphan_rootm_branch). That cleanup is
      already tracked at `/plans/active/issues/reference_path_convention_2026_07_23.md` (`status: open`, 6 todos,
      explicitly scoped to drive `format_count` to 0) — not a new finding, not this archival's scope to absorb.
      Evidence: `unified-trading-pm@aea497b5f` (content commit) + `unified-trading-pm@<pending-sha>` (this git-mv
      commit).

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

- **2026-07-31 (slot 15, review craft)** — dispatched todo 3 (E7/E11-E13 re-verify). E7/E11/E13 all re-confirmed still
  in their recorded state (unchanged) — E7 corroborated by the sibling doc's own fresh 2026-07-31 na-eligibility-audit
  verdict, E13 by its source doc's 2026-07-30 verdict. **E12 had silently changed** — its source doc
  (`ci_test_content_and_tooling_speed_findings_2026_07_28.md`) is now fully resolved + archived, all 5 `[UI]` todos
  done; rewrote the E12 row in `ci_satellite_ao_dispatch_batch2_2026_07_29.md`'s Deferred table to record RESOLVED so
  todo 4 doesn't need to migrate it forward. See todo 3's own inline evidence for full citations. Todo 4 (archival) is
  next in the `sequential: true` chain — final step of this finalize plan.
