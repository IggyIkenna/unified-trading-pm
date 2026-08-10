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
- [x] ✅ [REVIEW] P2. **Spot-check 3 of the 14 REOPEN-or-FLIP verdicts against the actual evidence** (the cited
      `done_sha` + the plan's real content), independently — not re-trusting the triaging worker's own claim. Prioritize
      the ones flagged in-doc as ambiguous: `mtds_migrate_executor_progress_checkpoint_gap-009`/`-010` (shared
      `done_sha`), and the two explicitly gate-shaped rows (`cefi_track2_backfill_vm_preempted_no_recovery-003`,
      `deployment_scripts_bucket_soft_delete_retention_drift-002`). **Done when**: each spot-checked row's verdict is
      independently confirmed correct, or a discrepancy is reopened/corrected with evidence. **VERIFIED 2026-08-10 (slot
      11, review)**: all 4 spot-checks independently CONFIRMED the verdicts — full evidence in Progress Log.
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
- **2026-08-10T16:20Z (slot 22, backend_engineer, task
  `ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08_finalize-28aa3f5fc829`)**: **Todo 1 (re-run
  audit_false_done.py) is NOT done — the audit is genuinely RED. NOT flipping.** Re-ran
  `scripts/orchestrator/audit_false_done.py` against the LIVE DB
  (`/home/ubuntu/unified-trading-system-repos/agent-orchestrator/data/state/state.db`, 306MB, the file the running
  orchestrator process holds open), plans read at `origin/live-defi-rollout`:
  **`false_done 16 · honest 914 · UNAUDITABLE 11 · unresolved 1528`, exit code 1**. The `.service` unit has NO
  `SuccessExitStatus=1`, so exit 1 is the genuine-breach signal — the finalize premise ("confirm audit exits 0 ...
  before archiving") is NOT met. The 16 rows are a RECURRENCE + growth vs the parent's 14: 2 overlap the triaged set
  (`defi_cefi_venue_chain_axis_contamination-011` now `done_sha=no-code:gate-still-unmet-verified`,
  `cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed-025` now `done_sha=0e9185d2c` — both re-done
  with checkbox still `- [ ]`), 14 are NEW, and unresolved grew 1,013→1,528. **Do NOT archive the parent doc** — the
  audit is not clean. Filed the full finding + per-row reopen/FLIP todos in
  `plans/archive/issues/audit_false_done_16_rows_still_red_2026_08_10.md`. This todo stays `- [ ]` until a fresh audit
  re-run exits 0 after the 16 rows are triaged.
- **2026-08-10 (slot 11, review, task `ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08_finalize-002`)**:
  **Todo 2 done — all 4 spot-checks (3 groups) independently CONFIRMED.** (1)
  `mtds_migrate_executor_progress_checkpoint_gap-009` — `6ddb0374` is a real on-origin commit (slot-8,
  `feat(mtds): add record_vm_progress checkpoint to migrate_sports_casing_revert_2026_07_27.py`, ancestor of
  `origin/live-defi-rollout`), `record_vm_progress` import + call confirmed present in the revert script at origin, and
  the plan's Category A todo is `[x]` ✅ citing `6ddb0374` accurately (no -008-style citation defect). (2) `-010` — the
  audit-time shared `6ddb0374` was genuinely a copied-sha defect (that commit belongs to -009's revert script); at
  verdict time no `record_vm_progress` existed in `migrate_sports_league_id_casing_2026_07_21.py` and the todo was
  `- [ ]`, so "no REOPEN/FLIP" was correct then; since then `3ec92a02` (2026-08-08, slot-10) added the checkpoint and
  the todo is now honestly `[x]` ✅ citing it — the real work the verdict kept live in the backlog was picked up and
  shipped. (3) `cefi_track2_backfill_vm_preempted_no_recovery-003` — gate-shaped todo (line 178) still `- [ ]`, gate
  ("relaunched VM genuinely completes, measured exit") genuinely unmet (8th relaunch 2026-08-09), and no live `done`
  backlog row holds the id — nothing to REOPEN, FLIP would be a false done. (4)
  `deployment_scripts_bucket_soft_delete_retention_drift-002` — `97d37ce57` is a real on-origin commit (slot-6,
  `docs(plans): exact - [x] brief match for 08-06 pre-gate verification flip`) that flipped the PRE-GATE checkpoint
  (line 104, `[x]`, explicitly "NOT the final drain"); the real final-drain todo (line 114) is still `- [ ]`, date-gated
  to on/after 2026-08-09. All 4 ids are absent from the live 3,168-row backlog. No discrepancy to reopen or correct.
