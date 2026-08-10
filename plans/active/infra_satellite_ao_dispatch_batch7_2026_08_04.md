---
doc_type: plan
title:
  Infra satellite AO batch 7 — 3 conflict-clear extractions from the 2026-08-03 never-cited candidates
  (na-eligibility-audit false-positive fix + interim doc mitigation, and a bounded terraform-history investigation)
summary: >-
  Seventh AO-dispatch batch for the `infra` topic tranche, produced by `/ag-closeout-audit infra` (autonomous mode,
  2026-08-04). Phase 0 re-derived the covering set (13 covering docs, unchanged since 2026-08-02; 50 members, up from 45
  on 2026-08-03) via `generate_ag_closeout_audit_candidates.py --tranche infra`: exactly 3 never-cited candidates, all
  created 2026-08-03 and read for the first time this run (none existed yet when yesterday's 45-agent Phase 1 sweep
  ran). Of the 3: one (`ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`) is a large, actively-executing live
  VM-migration human plan — genuinely non-batchable (too-large-or-risky / actively-draining-process taxonomy), not
  extracted. The other two contribute 3 conflict-clear, bounded todos: both `[SCRIPT]`/`[DOCS]` items from
  `na_eligibility_incremental_diff_false_positive_on_frontmatter_only_backfills_2026_08_03.md` extract directly (source
  doc already scoped them as bounded, worker-determinable, with a decided fix approach); the third extracts ONLY the
  bounded investigation half of `deployment_service_live_event_log_disconnected_tofu_root_2026_08_03.md`'s single todo —
  its own text explicitly separates a worker-doable git-history read from an operator-only structural decision, so this
  batch dispatches the former and leaves the latter gated. Re-verified all 3 still-open carried-forward `[OPERATOR]`-
  tagged findings from `ag_closeout_audit_infra_parked_2026_08_03.md` live before this triage (findings 6, 10, 11 — none
  resolved since yesterday); not re-drafted here, they remain operator-gated exactly as reported.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm, deployment-service]
scope: [engineer, admin]
tags: [infra, ao-dispatch, ag-closeout-audit, satellite-docs, batch-7, plan-hygiene, na-eligibility-audit, terraform]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch7_finalize_2026_08_04.md,
    /plans/archive/issues/na_eligibility_incremental_diff_false_positive_on_frontmatter_only_backfills_2026_08_03.md,
    /plans/archive/issues/deployment_service_live_event_log_disconnected_tofu_root_2026_08_03.md,
    /plans/archive/2026_08/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_08/issues/ag_closeout_audit_infra_parked_2026_08_03.md,
    /plans/archive/2026_08/issues/ag_closeout_audit_infra_parked_2026_08_04.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-04"
last_updated: "2026-08-06"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.7
estimate_calibrated_ai_days: 0.56
assigned_role: infra
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/archive/issues/na_eligibility_incremental_diff_false_positive_on_frontmatter_only_backfills_2026_08_03.md,
    /plans/archive/issues/deployment_service_live_event_log_disconnected_tofu_root_2026_08_03.md,
    scripts/plan-hygiene/generate_na_doc_tranche_inventory.py,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    deployment-service/terraform/gcp/live_event_log/main.tf,
    /plans/active/infra_satellite_ao_dispatch_batch7_finalize_2026_08_04.md,
  ]
source: >-
  `/ag-closeout-audit infra` run 2026-08-04 (ag_closeout_auditor scheduled worker, slot 10). Phase 0 re-derived the
  covering set (13 covering docs, unchanged; 50 members, 3 never-cited) via `generate_ag_closeout_audit_candidates.py
  --tranche infra`. Phase 1 direct-read all 3 never-cited docs (targeted delta read, not a full re-sweep — matches this
  tranche's own established precedent for small single-day deltas following a comprehensive baseline sweep the day
  before, 2026-08-03's 45-agent Workflow). Phase 3 applied the dispatch-scope eligibility test + the HARD conflict check
  (grepped all 13 existing infra covering docs + a corpus-wide filename/keyword grep for each candidate's target files)
  before drafting anything here. See `issues/ag_closeout_audit_infra_parked_2026_08_04.md` for the full per-doc
  classification and the non-batchable item's reasoning.
---

# Infra satellite docs — AO dispatch batch 7

## Why this plan exists

3 never-cited candidates surfaced this run, all created 2026-08-03 (too new for yesterday's sweep). Reading all 3 in
full:

- `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md` — a large (6 open todos), operator-approved, currently
  **actively executing** human plan (self-declared `assigned_vm: NA` / `execution_scope: local-only` because "each phase
  gate is a live judgment call, not a determinable worker todo"): a real VM migration (self-hosted CI-runner fleet off
  the AO box), live AWS billing decisions, a 4h-deferred VM-termination timer, and an in-progress batched runner
  migration (6/21 pools done as of 2026-08-03) with an explicit hard-sequencing rule. This is the non-batchable
  taxonomy's "too-large-or-risky-for-a-batch-todo... an actively-draining process" category verbatim — folding even its
  cleanest-looking remaining todo (e.g. the P2 codex-doc update) into a batch risks colliding with the plan's own live
  execution state. **NOT extracted.**
- `na_eligibility_incremental_diff_false_positive_on_frontmatter_only_backfills_2026_08_03.md` — a
  `/na-eligibility-audit` self-filed issue doc, explicitly scoped by its own author as "a clean candidate for a future
  pass to... flip to `assigned_vm: planning`" (deliberately not self-reclassified in the same breath per the two-step
  precedent it cites). Both of its todos are bounded, name a single target file each, state a decided fix approach, and
  carry an explicit Done-when. **Both extracted directly.**
- `deployment_service_live_event_log_disconnected_tofu_root_2026_08_03.md` — a deferred follow-up from an already-
  resolved parent issue, asking whether `deployment-service/terraform/gcp/live_event_log/` is intentionally a standalone
  OpenTofu root or an historical accident, given its own misleading "inherited from parent" comment. The doc's own
  "Recommended decision" section explicitly splits this: "A worker CAN do the git-history investigation (bounded,
  checkable) and report findings; the decision on whether to consolidate the roots is the human judgment call, hence
  `assigned_vm: NA`." **Only the investigation half is extracted** — the (a)/(b) structural decision stays gated exactly
  as the source doc itself frames it (see Deferred section below).

## Conflict check (before drafting)

Grepped all 13 existing infra covering docs (hub + batch1-6 + their finalize twins +
`infra_capture_and_devops_leftovers`/finalize) and the whole active corpus for both target file sets — no other covering
doc or in-flight plan claims either:

- `scripts/plan-hygiene/generate_na_doc_tranche_inventory.py` / `cursor-configs/skills/na-eligibility-audit/SKILL.md`'s
  Phase 0 section — the only corpus hits outside the source doc itself are unrelated `related:`-list citations (e.g.
  `infra_satellite_ao_dispatch_batch2_2026_07_27.md` cites the SKILL.md path in its own frontmatter `related:`, but none
  of that batch's actual todos touch Phase-0/content-hash logic) and other docs discussing the sibling
  `generate_ag_closeout_audit_candidates.py` script (a different script, same directory family) — no real overlap.
- `deployment-service/terraform/gcp/live_event_log/main.tf` (the root's own module/backend declaration + the misleading
  inheritance comment) — `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md` (`status: active`, 3 open
  todos) touches the SAME directory but only `warm_sink.tf`/`compaction_job.tf` (applying/recreating Pub/Sub resources
  inside the root), never `main.tf`'s own module/backend/comment block — verified its 3 open todos individually, none
  reference `main.tf` or the module-wiring question. No file-level collision with the investigation-only todo below.

No competing claim on either target-file set. All 3 todos below touch entirely different files from each other and from
every other in-flight plan — safe to run concurrently (no `sequential: true`).

## Todos

- [x] ✅ [SCRIPT] P3. **Implement content-hash (frontmatter-blind diff) verification in
      `scripts/plan-hygiene/generate_na_doc_tranche_inventory.py`'s incremental-mode output**, per the source doc's own
      "Recommended fix" option 1 (preferred: record a body-content hash — frontmatter stripped or at minimum excluding
      `context_scope:` — alongside each verdict marker; skip a doc on the next run when the current hash matches,
      regardless of intervening frontmatter-only commits). Done when: a doc whose only post-marker change is a
      `context_scope:` backfill (or any other frontmatter-only edit) reports as unchanged/skippable rather than
      in-scope, verified against at least the 5 docs named in the source doc's measurement table
      (`gitignore_sync_script_destructive_due_to_stale_central_template_2026_07_27.md`,
      `plan_reconcile_autonomous_sweep_2026_07_30.md`,
      `prod_vm_launch_missing_service_account_user_grant_2026_08_02.md`,
      `shared_host_home_filesystem_full_2026_07_26.md`,
      `stale_agentwork_scratch_clone_not_deletable_unpushed_stashes_2026_07_30.md`); a unit/regression test pins the
      distinction. Source:
      `issues/na_eligibility_incremental_diff_false_positive_on_frontmatter_only_backfills_2026_08_03.md` (todo 1).
      (repo: unified-trading-pm) — unified-trading-pm@7a75115ef; 22/22 tests pass; 3/3 active measurement-table docs
      report incremental_skip=True (2 others archived, no longer in active scan scope)
- [x] ✅ [DOCS] P3. **Update `cursor-configs/skills/na-eligibility-audit/SKILL.md`'s Phase 0 section** to instruct
      verifying an "in scope via date-fallback" doc's actual diff (`git show <marker-commit>..HEAD -- <path>` or
      equivalent) before trusting the date comparison, as an interim mitigation until the SCRIPT todo above lands. Done
      when: the skill file's Phase 0 section states this explicitly. Source:
      `issues/na_eligibility_incremental_diff_false_positive_on_frontmatter_only_backfills_2026_08_03.md` (todo 2).
      (repo: unified-trading-pm) — unified-trading-pm@afa14d4eb; Phase 0 now states the diff-verification step
      explicitly
- [x] ✅ [INFRA] P3. **Investigate (read-only) whether `deployment-service/terraform/gcp/live_event_log/` was ever wired
      as an actual `module "live_event_log" { source = "./live_event_log" }` block of the parent `terraform/gcp/`
      root.** Run `git log --follow` / `git blame` on `live_event_log/main.tf:9`'s inheritance comment and on the parent
      `main.tf` around when `live_event_log/` was first added. Report findings (whether a module block ever existed and
      was removed, or the directory was always structured this way) into
      `issues/deployment_service_live_event_log_disconnected_tofu_root_2026_08_03.md`'s own Progress Log — **do NOT
      apply either fix (a) [correct the comment] or (b) [wire a real module block] — that (a)/(b) choice stays an
      explicit `[OPERATOR]` decision**, per the source doc's own "Recommended decision" framing. Done when: the source
      doc's Progress Log carries a dated finding stating what the git history actually shows, and its Todos section is
      updated to reflect that the investigation is complete and only the (a)/(b) decision remains open. Source:
      `issues/deployment_service_live_event_log_disconnected_tofu_root_2026_08_03.md` (todo 1, investigation portion
      only). (repo: deployment-service investigation, unified-trading-pm doc update) — investigation complete per source
      doc Progress Log 2026-08-08: `live_event_log/` was intentional isolation from day one (commit fc7047c7 added it
      with its own backend/provider blocks; no `module "live_event_log"` ever existed in parent root's history). Source
      doc todo `[x] ✅` and Progress Log updated. Mechanical comment-fix follow-up remains for a deployment-service
      dispatch (named in source doc).

## Deferred — non-batchable this round

- **`deployment_service_live_event_log_disconnected_tofu_root_2026_08_03.md`'s (a)/(b) structural decision** —
  OPERATOR-GATED by the source doc's own explicit framing (not a mechanical fix; "needs an operator/architect call").
  The todo above extracts only the investigation half; once it lands, the decision becomes a normal, much-narrower
  `[OPERATOR]` follow-up on the source doc itself (handled by this batch's finalize plan, not re-drafted here).
- **`ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`** — GENUINELY HUMAN/OPERATOR-OWNED, actively executing real
  infra (see "Why this plan exists" above). Will keep reporting orphaned until the plan itself completes or the operator
  explicitly carves out a bounded sub-item — an accurate signal, not a stuck audit.
- **Carried-forward `[OPERATOR]` findings from `ag_closeout_audit_infra_parked_2026_08_03.md`** (re-verified live this
  run, all still open, unchanged): finding 10 (`infra_satellite_ao_dispatch_batch3_2026_07_30.md`'s `assigned_vm` still
  landed blank, not `planning`), finding 11 (the `instruments-service-agentwork-sports-2026-07-13` stash-backup bundle
  still genuinely absent anywhere on-host), and the tranche-level `BLOCKED-OPERATOR-DECISION`
  (`ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md`'s `asset_group` mistag, options A/B/C still
  unresolved, tracked in `infra_consolidated_closeout_2026_07_25.md`'s own Progress Log). None re-drafted here — see
  `issues/ag_closeout_audit_infra_parked_2026_08_04.md` for this run's full re-verification.

## Operator approval gate

**This plan is `status: active` — operator-approved 2026-08-06, dispatching (its todos 1-2 duplicate work also tracked
in `na_eligibility_incremental_diff_false_positive_on_frontmatter_only_backfills_2026_08_03.md`; that source doc's own
finalize twin will citation-close them, per the operator's explicit ruling — no separate action needed here).** Flipped
from `draft` (its finalize twin, already `status: active` per the no-double-gate ruling) to `status: active` is the
operator's call. All 3 todos above are read-only-investigation / narrowly-scoped-mechanical-fix with no `[OPERATOR]` tag
needed on their own merits — the draft gate here is solely the standing "a skill-drafted AO batch needs explicit
operator sign-off before dispatch" rule, not a signal any todo itself is risky.

## Codex SSOTs (read before touching a todo)

- `/cursor-configs/skills/ag-closeout-audit/SKILL.md` — the procedure this batch was produced by
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — the conflict-check protocol applied
  above
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — archival ritual the finalize plan runs
- `/plans/active/task_template.md` §4 — finalize-plan-coverage rule, dispatch-scope eligibility test

## Progress Log

- **2026-08-04** — Drafted by `/ag-closeout-audit infra` (autonomous mode, scheduled daily run, slot 10) after the 3
  net-new (2026-08-03-created) never-cited candidates were classified. Re-verified all 3 carried-forward `[OPERATOR]`
  findings from `ag_closeout_audit_infra_parked_2026_08_03.md` live first (per the iterative-drain methodology's step 1)
  — all 3 still open, unchanged, not re-drafted. Paired with `infra_satellite_ao_dispatch_batch7_finalize_2026_08_04.md`
  in the same run per the finalize-plan-coverage rule.
- **context-scout 2026-08-07**: refreshed context_scope (6 entries) — swapped the parked-findings pointer for the 3 open
  todos' actual source docs and code targets (both `na_eligibility_incremental_diff_...` and
  `deployment_service_live_event_log_...` source issue docs, `generate_na_doc_tranche_inventory.py`,
  `na-eligibility-audit/SKILL.md`, and `live_event_log/main.tf`).
- **2026-08-08** — todo 2 ([DOCS] P3) complete: added date-fallback diff-verification guidance to Phase 0 of
  `cursor-configs/skills/na-eligibility-audit/SKILL.md` — unified-trading-pm@afa14d4eb.
- **2026-08-08** — todo 3 ([INFRA] P3) complete: git-history investigation confirms `live_event_log/` was intentional
  isolation from the start (commit fc7047c7 added it with its own `backend "gcs"` + `provider "google"` blocks; no
  `module "live_event_log"` block ever existed in the parent root at any point in history). Source doc Progress Log and
  Todos updated accordingly. Remaining mechanical fix (correct the misleading "inherited" comment in
  `live_event_log/main.tf:9`) named explicitly for a deployment-service dispatch in the source doc.
