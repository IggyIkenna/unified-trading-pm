---
doc_type: plan
title: Finalize the terminal-status archival backlog sweep — reconcile evidence, re-check deferrals, close the ratchet
summary:
  Companion finalize plan for terminal_status_archival_backlog_sweep_2026_07_25.md (task_template.md's "every
  AO-dispatched plan needs a gated finalize plan" rule). Runs once the sweep's 66 archival todos are all done — re-
  verifies every archived doc's referrer fixup actually landed, re-checks any BLOCKED-OPERATOR-DECISION item parked
  mid-sweep, shrinks the check_terminal_status_archived.py ratchet baseline to the new (ideally zero) live count, and
  archives the sweep plan itself once fully done.
status: draft
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [archival, plan-hygiene, issue-lifecycle, backlog-sweep, finalize]
related:
  [
    /codex/11-project-management/issue-doc-lifecycle.md,
    /plans/active/terminal_status_archival_backlog_sweep_2026_07_25.md,
  ]
created: 2026-07-25
last_updated: 2026-07-25
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: infra
drift_direction: advance-code
sequential: true
depends_on: [terminal_status_archival_backlog_sweep_2026_07_25]
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "task_template.md §4 finalize-plan-coverage rule, authored alongside
  terminal_status_archival_backlog_sweep_2026_07_25.md"
---

# Finalize the terminal-status archival backlog sweep

`status: draft` until the sweep plan is dispatched and progressing — flip to `active` once the sweep's todos start
landing (draft-gated, per task_template.md §4; regen skips drafts so this never floods the backlog prematurely).

## Todos

- [ ] [INFRA] P2. Re-run `python3 scripts/plan-hygiene/check_terminal_status_archived.py` (no `--quiet`) and confirm
      every one of the 66 originally-flagged paths is gone from the live violation list — for any that remain, read the
      sweep plan's Progress Log to see whether it's a genuine `BLOCKED-OPERATOR-DECISION` park (leave it) or a missed
      todo (finish it here). Done when: the live count equals the number of genuinely-parked items (0 in the common
      case).
- [ ] [INFRA] P2. For every archived doc, re-verify its corpus-wide referrer fixup actually landed —
      `grep -rln     "<old-basename>" --include="*.md" plans/ codex/` must return zero hits outside the archived file's
      own new location. Fix any remaining stale reference found. Done when: the grep is clean for all 66 (or all minus
      parked items).
- [ ] [INFRA] P2. Run `python3 scripts/plan-hygiene/check_terminal_status_archived.py --update-baseline` to shrink
      `terminal_status_archived_baseline.yaml`'s `violation_count` to the new live count (ideally 0). Done when: the
      baseline file reflects the post-sweep count, committed.
- [ ] [INFRA] P2. Run the full `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` and confirm zero hard failures
      before closing this plan. Done when: sweep output shows `Hard failures: 0`.
- [ ] [INFRA] P2. Archive `terminal_status_archival_backlog_sweep_2026_07_25.md` itself per the standard 6-step archival
      ritual (it will be `status: complete` by the time this todo runs) — banner, `git mv` to `plans/archive/`, fix any
      referrer to it (likely none — this is a leaf sweep plan). Done when: the sweep plan no longer appears in
      `plans/active/` and `check_terminal_status_archived.py` stays green with it gone.
