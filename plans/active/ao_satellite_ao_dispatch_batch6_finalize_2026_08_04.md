---
doc_type: plan
title: AO satellite AO batch 6 — finalize
summary: >-
  Gated closeout for ao_satellite_ao_dispatch_batch6_2026_08_04.md — machine-held via depends_on + gate_on_depends until
  every todo in that batch is done. Reconciles each completed todo's evidence back into its TRUE source issue doc(s)
  (the batch was an extraction, so the source docs' own checkboxes are the ones that go stale), re-checks whether any of
  the 45 declined-orphan docs' named gates have since cleared, archives the source docs that reach zero open todos, and
  runs the standard 6-step archival ritual on the batch plan itself.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-6, finalize]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch6_2026_08_04.md,
    /plans/active/ao_satellite_ao_dispatch_batch5_2026_08_03.md,
    /plans/active/ao_satellite_ao_dispatch_batch5_finalize_2026_08_03.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-04"
last_updated: "2026-08-04"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: review
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_satellite_ao_dispatch_batch6_2026_08_04]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/ao_satellite_ao_dispatch_batch6_2026_08_04.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored in
  the same turn as its batch by the /ag-closeout-audit ao skill run of 2026-08-04. Ships `status: active` (not draft)
  per the skill's 2026-07-30 finding: `gate_on_depends` already machine-holds every task until the batch's own todos are
  done, so a second draft-gate is a redundant, easy-to-forget manual flip — only the batch itself (genuinely unreviewed,
  judgment-laden content) needs `status: draft` + explicit operator approval.
---

# AO satellite AO batch 6 — finalize

> **Machine-gated on `/plans/active/ao_satellite_ao_dispatch_batch6_2026_08_04.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until every todo in that batch is `done`. The batch itself stays
> `status: draft` until the operator approves it; this finalize plan needs no separate flip either way.

## Todos

- [ ] [REVIEW] P0. **Re-verify every batch-6 done-claim against reality, not against its checkbox** — for each of the
      10 todos in `/plans/active/ao_satellite_ao_dispatch_batch6_2026_08_04.md`, re-run `git show --stat <sha>` for
      every cited commit and re-run the specific named test(s) directly rather than trusting the claim, and re-run each
      todo's own stated done-when check where it is a command. **Done when**: all 10 verified, and any claim whose
      evidence does not hold up is re-opened as a new tracked todo in this doc's Progress Log with the discrepancy
      stated.
- [ ] [REVIEW] P0. **Reconcile each verified todo's evidence back into its TRUE source doc's own checkbox(es)** — batch
      6 was an extraction, so the source-doc items it covers are the ones that go stale, not the batch's. Flip the
      specific todo(s) in each of: `ao_open_issues_consolidated_close_out_2026_07_17.md` (Phase-8 items 5+6 only),
      `ao_done_gate_no_carveout_for_red_gate_evidence_only_closure_2026_07_28.md` (its sole item),
      `external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25.md` (its sole item),
      `orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md` (its 2nd `[BACKEND] P3` item only),
      `wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md` (its 2 remaining items),
      `boot_composer_misroutes_lifecycle_roles_into_worker_boot_branch_2026_07_31.md` (all 3 items — 1st+3rd combined,
      2nd separate), `fleet_git_health_ip_185_known_human_planning_vm_2026_08_03.md` (its sole item), and
      `na_and_ag_closeout_audit_population_overlap_2026_07_31.md` (its 1st item only). **Done when**: every one of
      those flips is committed with the `docs(plans):` prefix and cites the real commit sha.
- [ ] [INFRA] P0. **Re-check whether any of the 45 declined-orphan docs' NAMED gate has cleared since 2026-08-04, and
      spin any newly-conflict-clear items into batch 7** — walk the batch's own "Deferred — the 45 declined orphans"
      section category by category: has any operator-gated design fork been ruled since? Has any credential/host-access
      gap closed? Has the 3 conditionally-gated orthogonality-sweep items (`orphaned_wip_slot12_slot8_recovery`'s 2nd/
      3rd items, gated on main's confirmation) been resolved? Per this skill's iterative-drain methodology, re-check the
      SPECIFIC named gate on each, don't re-derive the classification from scratch. **Done when**: each of the 45 (+3
      conditional) is marked cleared-and-moved (naming the new batch-7 plan/todo) or still-gated with the current
      reason — no entry left unstated.
- [ ] [REVIEW] P0. **Archive every source doc that has reached zero open todos, and repoint any referrer.** At minimum
      re-check all 8 source docs named in todo 2 above for whether their OTHER (non-batched) items are also closed —
      several (e.g. `ao_open_issues_consolidated_close_out_2026_07_17.md`, `boot_composer_misroutes...`) have
      additional open items NOT covered by this batch and must NOT be archived if so. Run the standard 6-step archival
      ritual (migrate any DEFERRED item → banner → codex-alignment check → fix every referrer's path corpus-wide →
      clear the lock) on any doc that IS fully done. **Done when**: `grep -rl <slug> plans/ codex/` returns only the
      archived copy's own path for each archived doc, and `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports
      zero NEW hard failures (compare against the baseline recorded at this finalize plan's authoring time).
- [ ] [INFRA] P0. **Run the 6-step archival ritual on the batch plan itself, then regenerate the inventory** — banner
      `/plans/active/ao_satellite_ao_dispatch_batch6_2026_08_04.md`, migrate any still-open Deferred item into batch 7
      (never leave a deferral that is not already a `- [ ]` todo somewhere), move the file to `plans/archive/2026_08/`,
      fix every corpus-wide referrer including this finalize plan's own `related:`/`depends_on:`, then run
      `.venv/bin/python scripts/plans/regenerate_active_plan_inventory.py --commit` (verify the exact entrypoint name at
      execution time). **Done when**: the batch plan is archived with a banner, the inventory regenerates cleanly, and
      `check_finalize_plan_coverage.py` no longer names this pair.

## Codex SSOTs

`/codex/11-project-management/` (findings triage + the archival ritual),
`/codex/11-project-management/cross-reference-path-convention.md` (the corpus-wide referrer fixup),
`/codex/12-agent-workflow/commit-push-flip-rule.md` (evidence-backed flips),
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility".

## Progress Log

- **2026-08-04** — Authored in the same turn as its batch by `/ag-closeout-audit ao` (autonomous mode, scheduled
  dispatch). `sequential: true` is deliberate here: the five todos are a genuine chain (verify → reconcile → re-check
  gates → archive sources → archive self) and several touch the same files. Ships `status: active` per the skill's
  2026-07-30 finding (`gate_on_depends` already holds every task; no separate draft-gate needed).
