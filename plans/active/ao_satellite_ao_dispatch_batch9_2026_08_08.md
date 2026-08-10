---
doc_type: plan
title: AO satellite AO batch 9 — ninth dispatch batch, one gate-clearance finding from batch6-finalize's re-check
summary: >-
  NINTH AO-dispatch batch for the `ao` topic tranche. Unlike batch5-8 (each a fresh `/ag-closeout-audit ao` fan-out),
  this batch was produced by `ao_satellite_ao_dispatch_batch6_finalize_2026_08_04.md`'s own todo 3 — a named-gate
  re-check of all 45 declined-orphan docs + 3 conditional items from batch6's Deferred section, per the skill's
  iterative-drain methodology ("re-check the SPECIFIC named gate on each, don't re-derive the classification from
  scratch"). Of 48 items re-checked, exactly ONE surfaced genuinely new, not-yet-extracted AO-eligible work:
  `review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md`'s 2 remaining items, whose 2nd stated conflict
  (sequencing behind `boot_composer_misroutes_lifecycle_roles_into_worker_boot_branch_2026_07_31.md`'s composer-guard
  fix) cleared today when that fix's code landed live (`agent-orchestrator@6166269`/`@0a8ed16`, verified via
  batch6-finalize todo 1's own re-run evidence) even though the source doc's own checkboxes are still stale-unflipped (a
  separate, already-tracked reconciliation gap, not this batch's job). Every other cleared/resolved item found by the
  re-check was either already self-dispatched (`assigned_vm: planning` directly, no batch wrapper needed), fully
  resolved with zero remaining work, or a stale-checkbox-only situation with no new AO-eligible work — none needed a
  batch extraction. Full per-item disposition of all 48 re-checked items lives in
  `ao_satellite_ao_dispatch_batch6_finalize_2026_08_04.md`'s Progress Log, not duplicated here.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-9, satellite-docs, gate-recheck]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch9_finalize_2026_08_08.md,
    /plans/active/ao_satellite_ao_dispatch_batch6_finalize_2026_08_04.md,
    /plans/active/ao_satellite_ao_dispatch_batch6_2026_08_04.md,
    /plans/active/ao_satellite_ao_dispatch_batch8_2026_08_08.md,
    /plans/archive/2026_08/issues/review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md,
    /plans/active/issues/boot_composer_misroutes_lifecycle_roles_into_worker_boot_branch_2026_07_31.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/archive/2026_08/issues/review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md,
    /plans/active/issues/boot_composer_misroutes_lifecycle_roles_into_worker_boot_branch_2026_07_31.md,
    agent-orchestrator/server/prompts.py,
    agent-orchestrator/server/routes/slots_worker.py,
    unified-trading-pm/agents/review.md,
    unified-trading-pm/agents/worker.md,
  ]
source: >-
  `ao_satellite_ao_dispatch_batch6_finalize_2026_08_04.md` todo 3 (2026-08-08, dispatch
  `ao_satellite_ao_dispatch_batch6_finalize-002`, slot 27, infra craft) — a full re-check of all 45 declined-orphan docs
  + 3 conditional items named in batch6's own Deferred section, checking each item's SPECIFIC stated gate rather than
  re-deriving classification. Ran via 4 parallel sub-agents covering the operator-gated (26), too-large (10), human-only
  (5), conflict-gated (6), and conditionally-gated (3) categories. Full findings archived in the finalize plan's
  Progress Log.
---

# AO satellite AO batch 9

> **`status: draft`** — pending operator approval, same convention as every prior batch (`gate_on_depends` on the
> finalize twin already machine-holds dispatch of the finalize plan; this batch itself still needs the explicit operator
> flip to `active` before its own todo enters the backlog, per the established batch5-8 precedent).
> **`assigned_vm: planning` / `execution_scope: orchestrator-agent`** — the `ao` tranche's 2026-07-17 "local execution
> only" ruling was lifted 2026-08-08 (see batch5/6/7/8's own Progress Logs for the citation trail); AO-dispatchable once
> approved, same as every other tranche in this series.

## Why this plan exists

`ao_satellite_ao_dispatch_batch6_finalize_2026_08_04.md`'s todo 3 required re-checking every one of batch6's 45
declined-orphan docs (plus 3 conditional items) for whether their SPECIFIC named gate has cleared since 2026-08-04 — not
re-running the classification from scratch. That re-check (2026-08-08) found:

- **~13 items already fully resolved/archived/superseded** with zero remaining work (e.g.
  `mtds_plan_flip_fabricated_commit_sha_evidence`, `two_agents_slot3_collision_and_yahoo_finance_red_tree`,
  `p1_2_backlog_hand_park_did_not_persist`, both OmniRoute docs via an explicit 2026-08-06 operator no-go ruling) —
  nothing to extract.
- **~9 items whose specific gate cleared via a fresh 2026-08-06/08-08 operator ruling, but the doc was ALREADY
  `assigned_vm: planning`** (directly reclassified by na-eligibility-audit or the ruling itself, not routed through a
  batch) — e.g. `blocked_questions_ux_redesign_context_loss_and_scale`, `long_lived_vm_logs_not_backed_up`,
  `multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout`, `git_health_not_clean_since_pinned_constant`,
  `utl_shared_clone_commits_repeatedly_reset`. These self-dispatch via the normal backlog regen — no batch wrapper
  needed.
- **1 stale-checkbox-only situation** (`orphaned_wip_slot12_slot8_recovery_2026_08_04.md`'s 2nd item — content already
  confirmed MOOT by 2026-08-06 `/plan-reconcile ao`, checkbox just never flipped) — doc hygiene, not new work; left for
  the normal reconciliation flow.
- **1 genuinely new AO-eligible finding**: `review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md`'s 2 remaining
  items. Both were held since 2026-08-02 on 2 named conflicts; the tranche-ownership retag conflict cleared 2026-08-02
  (already reflected in the doc's own `asset_group`), and the 2nd conflict — sequencing behind
  `boot_composer_misroutes_lifecycle_roles_into_worker_boot_branch_2026_07_31.md`'s composer-guard fix — cleared TODAY:
  that fix's code (`agent-orchestrator@6166269` extending `_REGISTER_POLL_ROLES` to `{review, main, monitor}` + one-shot
  lifecycle roles via `@0a8ed16`) is live and independently re-verified
  (`ao_satellite_ao_dispatch_batch6_finalize_2026_08_04.md` todo 1's own re-run:
  `test_register_poll_role_gets_slotless_shape_even_with_slot_id`
  - `test_one_shot_lifecycle_role_unaffected_by_register_poll_guard`, both passing). The source doc's own
    `boot_composer_misroutes...` checkboxes are still unflipped pending the finalize plan's own todo 2 reconciliation
    pass — that is a separate, already-tracked gap, not evidence the underlying fix is missing.
- **Everything else (the remaining ~35 items** — NOTE: arithmetic doesn't foot; the breakdown above totals 13+9+1+1=24
  resolved/cleared/stale/new, but the doc's own stated total is 48 (45+3), which would leave ~24 remaining, not ~35; the
  correct count was not independently re-verified by either plan_reconciler run that flagged this — the actionable
  conclusion is unchanged, 1 new AO-eligible finding) genuinely remains gated for the same reasons stated in batch6's
  Deferred section, or was updated to a fresh-but-still-open reason (e.g.
  `orchestrator_host_memory_exhaustion_4th_recurrence`'s primary item shipped but a NEW `[OPERATOR] P2` item was filed
  2026-08-07). Full per-item detail lives in `ao_satellite_ao_dispatch_batch6_finalize_2026_08_04.md`'s Progress Log —
  not restated here.

## Rules for every worker on this plan

- Do not edit `review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md`'s checkboxes beyond appending your evidence
  line to the todo you executed — the paired finalize plan
  (`/plans/active/ao_satellite_ao_dispatch_batch9_finalize_2026_08_08.md`) reconciles evidence back into the source doc.
- Before starting, re-pull `boot_composer_misroutes_lifecycle_roles_into_worker_boot_branch_2026_07_31.md` fresh and
  confirm its composer-guard fix is still live (it should already be — this batch's own drafting verified it via
  batch6-finalize todo 1's independent re-run) — if it has regressed, STOP and file a fresh issue doc instead of
  proceeding on a false premise.
- No todo below deletes prod data, mutates a GCS bucket, or launches a VM.

## Todos

- [x] ✅ [DOCS] P1. **Audit every craft/audit-role file in `unified-trading-pm/agents/*.md` against
      `server/prompts.py::expected_read_files`, and add the regression test proving the STEP-0 declared read-list stays
      in sync — one combined todo since the audit and its regression test are tightly coupled (the test's assertion IS
      the audit, made durable).** First re-confirm live which roles the composer-guard fix (`_REGISTER_POLL_ROLES` +
      `_ONE_SHOT_ESCALATION_ROLES` in `server/prompts.py`) now routes to the slot-less register/poll branch — those
      roles no longer need `worker.md` in their STEP-0 text at all (patching them to add it would be actively wrong per
      the source doc's own conflict note). For every OTHER craft/audit role whose
      `expected_read_files("worker", <slot_role>)` still resolves through the worker-boot branch and includes
      `worker.md` (the source doc names `na_eligibility_auditor.md` and `ag_closeout_auditor.md` as confirmed live
      victims as of 2026-08-01 — re-verify both against the CURRENT composer-guard classification, since
      `ag_closeout_auditor` may now be covered by the one-shot-lifecycle-role extension while `na_eligibility_auditor`
      may not be), confirm the file's own STEP-0/boot section explicitly instructs reading `worker.md` (mirroring
      `agents/review.md`'s already-corrected wording), patching any file still missing it. Then add the regression test:
      for every role file, assert its own declared STEP-0 read list (basenames) is a superset of
      `expected_read_files("worker", <that role's slot_role>)`'s basenames where the composer routes that role through
      the worker-boot branch (skip roles the guard now routes to register/poll — assert those do NOT require `worker.md`
      instead, so a future composer-guard regression is caught too). Also check whether the 2026-08-08 14:30-16:30Z live
      recurrence report (review_role_boot_read's own Progress Log, main agt-22de53 relaying) predates or postdates the
      composer-guard fix landing — if it postdates, that's a live regression and takes priority over the text-audit;
      file a fresh P0 issue doc instead of proceeding. **Done when**: the regression test passes for every current role
      file; the text-audit table (role file → covered-by-guard? → worker.md-in-STEP-0?) is recorded in the source doc's
      Progress Log; the 14:30-16:30Z recurrence timing question is answered; full `agent-orchestrator`
      `quality-gates.sh` green. Source:
      `/plans/archive/2026_08/issues/review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md` (both its remaining
      `[DOCS] P1` and `[BACKEND] P2` items, combined — tightly coupled per this todo's own reasoning). Repo:
      unified-trading-pm, agent-orchestrator.

## Deferred

None — this batch has exactly one item, extracted directly from batch6-finalize's own re-check. See that plan's Progress
Log for the full disposition of the other 47 items re-checked (none needed extraction).

## Codex SSOTs (read before starting a todo)

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`, `…/agent-orchestrator-overview.md`,
`/codex/04-architecture/agent-orchestrator-alerting.md`,
`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`,
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`.

## Progress Log

- **2026-08-08** — Authored by `ao_satellite_ao_dispatch_batch6_finalize_2026_08_04.md` todo 3 (dispatch
  `ao_satellite_ao_dispatch_batch6_finalize-002`, slot 27, infra craft). Full re-check of batch6's 45 declined-orphan
  docs + 3 conditional items via 4 parallel sub-agents, checking each item's specific named gate per the skill's
  iterative-drain methodology. Conflict-check ran against `plans/active/*.md` for `prompts.py`/`expected_read_files`
  mentions — found 2 unrelated hits (`ao_open_issues_consolidated_close_out_2026_07_17.md`'s already-`[x]`
  plan_health/plan_reconciler variant of the same underlying hardcoding bug;
  `context_scout_completion_and_plan_brainstorm_skill_2026_07_30.md`'s unrelated `KeyError` role-file-lookup fix) —
  neither collides with this todo's target files. Left `status: draft` deliberately — flipping to `active` is the
  operator's call, matching batch5-8's own precedent.
- **2026-08-09 (slot 30, backend_engineer/infra crafts) — todo 1 DONE**: full audit found zero gaps in the
  originally-anticipated direction (all 5 craft roles + `ag_closeout_auditor`/`na_eligibility_auditor` already correctly
  documented — this doc's own "may not be covered" uncertainty resolved: both ARE covered by the composer-guard fix). 2
  unanticipated live gaps found + fixed in the SAME pass (findings-triage: in-file → same-commit): (1)
  `cefi_reconciliation_auditor`/`cefi_mtds_smoke_tester` missing from `_ONE_SHOT_ESCALATION_ROLES` since their
  2026-08-05 addition to `plan_health.py` — `agent-orchestrator@5353b6b`; (2) `review.md`'s STEP-0 still claimed the
  live /boot gate enforces `worker.md` for it — stale post-`6166269` (review never calls `/boot` anymore), corrected to
  a historical note — `unified-trading-pm@6f7ed49c2`. 14:30-16:30Z 2026-08-08 recurrence PREDATES `6166269` (19:35Z that
  day) — not a live regression, no P0 filed. Regression test:
  `agent-orchestrator/tests/test_role_file_worker_md_read_sync.py`, full `quality-gates.sh` green (3060 tests + 262
  dashboard tests). Full audit table + evidence recorded in
  `/plans/archive/2026_08/issues/review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md`'s own todos/Progress Log
  per this plan's "Rules for every worker" (checkboxes there deliberately left unflipped for the finalize plan to
  reconcile).
