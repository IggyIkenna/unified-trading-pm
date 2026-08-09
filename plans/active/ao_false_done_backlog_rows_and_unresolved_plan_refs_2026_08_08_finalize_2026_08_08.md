---
doc_type: plan
title: audit-false-done 14 false-done rows + 1,013 unresolved plan_refs — finalize
summary: >-
  Gated closeout for `ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08.md` — machine-held via `depends_on`
  + `gate_on_depends: true` until all 17 of that doc's remaining todos (14 per-row REOPEN-or-FLIP verdicts + 3
  follow-ups) are done. Confirms `systemctl start audit-false-done.service` exits 0 with no new false-done rows
  introduced by the triage itself, before archiving.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao, agent-orchestrator, false-done, audit, close-out, archival, plan-hygiene]
related:
  [
    /plans/active/issues/ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08.md,
    /plans/epics/orchestrator_master.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.16
assigned_role: backend_engineer
effort: medium
drift_direction: advance-process
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08]
gate_on_depends: true
source: >-
  /na-eligibility-audit round7 RECLASSIFY sweep, 2026-08-08 — required companion per `plans/active/task_template.md`
  §4's finalize-plan-coverage rule (every AO plan needs a paired gated finalize).
context_scope:
  [
    /plans/active/issues/ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/PLAN_FORMAT.md,
  ]
---

# audit-false-done 14 rows + 1,013 unresolved plan_refs — finalize

> **Machine-gated on `ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08.md`** (`depends_on` +
> `gate_on_depends: true`) — the dispatcher will not queue any todo below until all 17 of the parent doc's remaining
> todos are `done`.

## Todos

- [ ] [REVIEW] P2. **Re-run `audit_false_done.py` live and confirm it exits 0** (or, if `SuccessExitStatus=1` semantics
      still apply, confirm `false_done: 0`) — per the parent doc's own explicit warning, do NOT "fix" this by changing
      the unit's exit-code contract; the unit exiting 1 on a genuine breach is correct behavior. **Done when**: a fresh
      live run against `state.db` is cited with the actual bucket counts, not assumed clean because the 14 named rows
      were triaged. Repo: agent-orchestrator (read-only verification).
- [ ] [REVIEW] P2. **Spot-check 3 of the 14 REOPEN-or-FLIP verdicts against the actual evidence** (the cited
      `done_sha` + the plan's real content), independently — not re-trusting the triaging worker's own claim. Prioritize
      the ones flagged in-doc as ambiguous: `mtds_migrate_executor_progress_checkpoint_gap-009`/`-010` (shared
      `done_sha`), and the two explicitly gate-shaped rows (`cefi_track2_backfill_vm_preempted_no_recovery-003`,
      `deployment_scripts_bucket_soft_delete_retention_drift-002`). **Done when**: each spot-checked row's verdict is
      independently confirmed correct, or a discrepancy is reopened/corrected with evidence.
- [ ] [DOCS] P2. **Archive the parent doc per the 6-step ritual, and only then.** Confirm zero open `- [ ]` todos
      remain; add the archival banner + set `status: complete`; grep the corpus for
      `ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08` and repoint every referrer; clear any lock if
      set. Then physically move the parent doc under `plans/archive/2026_08/`. **Done when**:
      `bash     scripts/plan-hygiene/run_hygiene_sweep.sh --ci --no-regen` is 0 hard, `check_reference_paths.py` shows
      no NEW dangling reference above its baseline, and `regenerate_active_plan_inventory.py` reports 0 orphans for this
      doc. Repo: unified-trading-pm.

## Codex SSOTs

`/codex/12-agent-workflow/commit-push-flip-rule.md` ·
`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (6-step ritual) · `plans/PLAN_FORMAT.md` ·
`plans/active/task_template.md` §4 (finalize-plan-coverage rule)

## Progress Log

- **2026-08-08**: Drafted alongside the parent doc's `na-eligibility-audit round7 RECLASSIFY` flip from
  `assigned_vm: NA` to `planning`. `status: active` immediately (not `draft`) — machine-held from actually dispatching
  via `depends_on` + `gate_on_depends: true` until the parent doc's 17 remaining todos are done.
