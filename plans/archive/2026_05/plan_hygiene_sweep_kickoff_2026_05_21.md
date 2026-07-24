---
doc_type: plan
title: Plan hygiene sweep — next-session kickoff prompt
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: []
related: [/plans/archive/2026_05/plan_hygiene_automation_2026_05_21.md]
created: "2026-05-23"
parent_epic: plan_hygiene_master
assigned_vm: vm-cross-cutting
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Next-Session Kickoff: Plan Hygiene Sweep

## Prompt to paste at session start

---

Run the plan hygiene sweep for `unified-trading-pm`. The hygiene scripts were created 2026-05-21 and live at
`scripts/plan-hygiene/`. Start by running:

```bash
cd /Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/1/unified-trading-pm
bash scripts/plan-hygiene/run_hygiene_sweep.sh
```

This will print a PASS/FAIL table. Then work through each failure category in order:

**1. Todo regression** (`check_todo_regression.sh`) Should currently be passing clean. If not, restore any regressed
plan from GitHub:

- Keep new frontmatter (head -N lines of current file)
- Restore GitHub body: `git show origin/live-defi-rollout:plans/active/<file> | tail -n +<gh_fm_end+1>`
- Combine and write back. Verify `^- \[ \]` count matches GitHub.

**2. Frontmatter violations** (`check_frontmatter.sh`) Many plans still have jammed frontmatter (`---title:` on one line
instead of `---` alone) and deprecated fields (`deadline`, `owner`, `asset_group`, `slug`, `horizon`, `companion_to`,
`companion_plans`, `spawned_from`). For each violating file:

- Split jammed `---key: val` → `---\nkey: val`
- Remove deprecated fields entirely
- Add missing required fields: `parent_epic`, `title`, `priority`, `status`, `estimate_class`,
  `estimate_baseline_ai_days`, `estimate_calibrated_ai_days`, `locked_by`
- DO NOT touch the body or any checkbox todos — only the frontmatter block (lines 1 to the closing `---`)
- After fixing, re-run `check_todo_regression.sh` to confirm no todos were lost

**3. Line cap violations** (`check_line_caps.sh`) For plans >1000L that are not umbrella plans (locked+>100 todos):

- Apply the writegate compression approach: remove DONE-\* handover sections, audit narratives, resolved Q&As — keep all
  `- [ ]` and `- [x]` checkboxes verbatim
- Target ≤1000L. Do NOT summarise checkbox content.

**4. Archive candidates** (`check_archive_candidates.sh`) 27 plans have 0 open todos and all checkboxes done. Review
each:

- Confirm there are genuinely no deferred items hiding in prose (grep body for `DEFERRED`, `TODO`, `BLOCKED`)
- If clean: `git mv plans/active/<file> plans/archive/2026_05/<file>`
- If deferred items found in prose: convert to `- [ ]` todos before archiving or keep in active

**5. Wire runbook into LEDGER morning boots** After sweep passes clean:

- Add `bash scripts/plan-hygiene/run_hygiene_sweep.sh` as first step in `ikenna_orchestrator/LEDGER.md` § "Morning boot
  sequence"
- Add same line to `harsh_orchestrator/LEDGER.md`
- Flip Phase 3 todos in `plans/active/plan_hygiene_automation_2026_05_21.md`

## Context from 2026-05-21 session

- 79 active plans were refactored by 6 parallel sub-agents to fix frontmatter and add `parent_epic`
- 5 plans had todo losses discovered and restored (writegate, aws_migration, batch_live_symmetry, tradfi_l1_l2_l3,
  agent_orchestrator_dual_deployment)
- The `check_todo_regression.sh` script now enforces zero regression at any future push
- Many plans still have jammed frontmatter — agents only partially succeeded due to prek auto-restore
- Epics README and plan format docs confirmed correct; plans/active/INDEX.md has supersession notice
- New epic: `plans/epics/plan_hygiene_master.md`
- Active plan tracking this work: `plans/active/plan_hygiene_automation_2026_05_21.md`

## Guiding rules for this session

- **Never summarise todos** — if a plan has `- [x] ✅ DEFERRED-OPERATOR-DECISION P0. Do X` and surrounding prose, keep
  the checkbox verbatim. Remove the prose, not the checkbox.
- **Fix frontmatter only** for jammed files — do not rewrite the body. Use Edit tool targeting only lines 1 to closing
  `---`.
- **Run `check_todo_regression.sh` after every batch of edits** — catch any accidental collapse immediately, not at the
  end.
- **Archive is irreversible** — only archive after confirming 0 open todos AND no deferred prose. When in doubt, keep in
  active.

## Deferred work — migrated to:

This plan was a next-session kickoff prompt — no active todos. The work it described has been executed in this session.

- Hygiene sweep guidance → `/codex/11-project-management/plan-hygiene.md` (SSOT)
- Script inventory → same codex doc + `scripts/plan-hygiene/`
- LEDGER wiring → superseded by Phase 6 daily cron approach (Cloud Run + Cloud Scheduler) Archiving 2026-05-23.
