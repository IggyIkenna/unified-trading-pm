---
doc_type: issue
title: sports_satellite_ao_dispatch_batch5 is over the 1000-line hard cap, blocking its priority-resort edit
summary:
  Discovered applying the 2026-07-28 priority-resort — sports_satellite_ao_dispatch_batch5_2026_07_26.md is already 1002
  lines (over the 1000-line hard cap) BEFORE the resort touched it, so `check_line_caps.sh` blocked staging its 1-line
  `priority:` edit. Excluded from that commit; left at its current priority pending the standard line-cap remediation
  (extract closed Progress Log sections into an archive-bound history doc, per plan_line_cap_remediation_2026_07_23.md's
  precedent).
status: open
nature: process
asset_group: [sports]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, line-cap, priority]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
    /codex/11-project-management/plan-priority-tier-and-dispatch-ordering.md,
  ]
created: "2026-07-28"
parent_epic: sports_master
source:
  Discovered mid-commit applying the 2026-07-28 priority-resort delta set; not fixed inline to avoid scope creep on that
  commit.
execution_scope: local-only
assigned_vm: NA
priority: P2
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# sports_satellite_ao_dispatch_batch5 is over the 1000-line hard cap

## Todos

- [ ] [SCRIPT] P2. Extract the oldest fully-closed dated Progress Log section(s) from
      `plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md` into an archive-bound
      `sports_satellite_ao_dispatch_batch5_history_2026_07.md` (`status: complete`, `nature: record`, 0 open todos)
      under `plans/archive/2026_07/`, leaving a one-line pointer behind, until the live doc is back under 1000 lines.
      Then flip its `priority:` from `P1` to `P2` per the 2026-07-28 resort (it is 21/23 top-level todos done, a
      corpus-hygiene AO-dispatch-batch satellite per that resort's carve-out logic, same as its sibling batches).
      Definition of done:
      `bash scripts/plan-hygiene/check_line_caps.sh plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md`
      reports the file within cap, and its `priority:` reads `P2`.
