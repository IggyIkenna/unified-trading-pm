---
doc_type: plan
title: Finalize the terminal-status archival backlog sweep — reconcile evidence, re-check deferrals, close the ratchet
summary:
  Companion finalize plan for terminal_status_archival_backlog_sweep_2026_07_25.md (task_template.md's "every
  AO-dispatched plan needs a gated finalize plan" rule). Runs once the sweep's 66 archival todos are all done — re-
  verifies every archived doc's referrer fixup actually landed, re-checks any BLOCKED-OPERATOR-DECISION item parked
  mid-sweep, shrinks the check_terminal_status_archived.py ratchet baseline to the new (ideally zero) live count, and
  archives the sweep plan itself once fully done.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [archival, plan-hygiene, issue-lifecycle, backlog-sweep, finalize]
related:
  [
    /codex/11-project-management/issue-doc-lifecycle.md,
    /plans/archive/terminal_status_archival_backlog_sweep_2026_07_25.md,
  ]
created: 2026-07-25
last_updated: 2026-07-25
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
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

> **Complete 2026-07-25** — all 5 todos done. The sweep plan archived 68 docs total (66 originally flagged + 4 that
> landed resolved mid-sweep), the check_terminal_status_archived.py baseline shrank to a true zero-tolerance 0, and a
> real duplicate-file bug from a rebase/stash race was caught and fixed along the way.

## Todos

- [x] [INFRA] P2. ✅ Re-ran `check_terminal_status_archived.py` repeatedly through the sweep's completion — confirmed 0
      violations against the 66-item baseline (plus 2 bonus docs that landed resolved mid-sweep and 2 more found
      afterward, all archived the same way). No BLOCKED-OPERATOR-DECISION parks were needed; every doc's
      resolution/supersession evidence held up. — unified-trading-pm@ad4b1952c (batch), @74313994b (dup-corruption fix),
      @0924a7d1c, @e0f1fb6a6.
- [x] [INFRA] P2. ✅ Re-verified corpus-wide referrer fixup via `check_reference_paths.py` (format 163/163, existence
      940/956 baseline — both within ratchet) and a full `run_hygiene_sweep.sh --ci` pass. One genuine duplicate-file
      bug was found and fixed mid-sweep (a rebase/stash-pop race resurrected 54 stale pre-archival copies back into
      plans/active/ alongside their correct plans/archive/ twins — diffed every pair to confirm no unique content, then
      removed the stale copies). — unified-trading-pm@74313994b, @0924a7d1c.
- [x] [INFRA] P2. ✅ Ran `check_terminal_status_archived.py --update-baseline` — `violation_count` shrunk from 66 to
      **0**, a true zero-tolerance gate going forward (not just a ratchet tolerating debt). — unified-trading-pm@(this
      commit).
- [x] [INFRA] P2. ✅ Full `run_hygiene_sweep.sh --ci` — `Hard failures: 0` confirmed (also picked up a new "No broken
      links" hard check and an improved existence-ref baseline of 956, both from other concurrent fleet work landing
      during the sweep). — verified unified-trading-pm@e0f1fb6a6.
- [x] [INFRA] P2. ✅ Archived `terminal_status_archival_backlog_sweep_2026_07_25.md` itself (banner + `git mv` to
      `plans/archive/`, its 2 live referrers repointed — this finalize plan's own `related:` entry and the
      active-plan-inventory-dashboard link). No longer in `plans/active/`; gate confirmed clean with it gone. —
      unified-trading-pm@74313994b, @0924a7d1c.
