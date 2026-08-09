---
doc_type: issue
title: MOVED — see plans/archive/2026_08/issues/promote_ref_orphaned_on_manual_pr_close_2026_08_06.md
summary: >-
  Redirect stub. The underlying issue resolved and archived 2026-08-09 to
  `plans/archive/2026_08/issues/promote_ref_orphaned_on_manual_pr_close_2026_08_06.md`. This stub's own status is
  `blocked`, not `resolved` — it is NOT the resolved issue itself, it is a permanent-until-unblocked placeholder kept at
  the old path solely because `plans/active/cross_cutting_consolidated_closeout_2026_07_25.md` links this exact path and
  is already over the 1000-line hard cap, so `check_line_caps.sh`'s SCOPED-mode append-only exception cannot accommodate
  a same-commit path-swap edit to that referrer (any modify — even a same-length path swap — needs `DELETED=0`, which a
  content replace never satisfies). Delete this stub once that referrer's line is repointed directly (tracked as a
  follow-up todo below) or once check_line_caps.sh gains a documented "referrer repoint after archival" exception.
status: blocked
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [redirect-stub, ci-cd]
related: [/plans/archive/2026_08/issues/promote_ref_orphaned_on_manual_pr_close_2026_08_06.md]
created: 2026-08-09
source: redirect-stub, cicd-worker-slot30, 2026-08-09
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
assigned_role: cicd
drift_direction: none
depends_on: []
locked_by:
locked_since:
resolved_by:
context_scope: [/plans/active/cross_cutting_consolidated_closeout_2026_07_25.md]
---

# Redirect stub

The underlying issue has been resolved and archived; this stub itself is `status: blocked` (not `resolved`) since it is
placeholder scaffolding, not closed work — see the Follow-up section for what unblocks its deletion. See
[`plans/archive/2026_08/issues/promote_ref_orphaned_on_manual_pr_close_2026_08_06.md`](/plans/archive/2026_08/issues/promote_ref_orphaned_on_manual_pr_close_2026_08_06.md)
for the full content and resolution evidence.

This stub exists only to keep `validate_plan_links.py` green against
`plans/active/cross_cutting_consolidated_closeout_2026_07_25.md`'s existing link to this path, since that file is
already over the `check_line_caps.sh` 1000-line hard cap and its SCOPED-mode exception only covers pure ≤10-line appends
with zero deletions — a same-line path-swap (1 line deleted, 1 line added) does not qualify.

## Follow-up

- [ ] [DOCS] P3. Repoint `plans/active/cross_cutting_consolidated_closeout_2026_07_25.md`'s link for
      `promote_ref_orphaned_on_manual_pr_close_2026_08_06.md` from this stub path to
      `/plans/archive/2026_08/issues/promote_ref_orphaned_on_manual_pr_close_2026_08_06.md` directly, then delete this
      stub file. Blocked today only by the line-cap-vs-broken-link gate conflict described above — either trim
      `cross_cutting_consolidated_closeout_2026_07_25.md` under 1000 lines first (unlocking a normal edit), or extend
      `check_line_caps.sh`'s SCOPED-mode exception to cover a bounded reference-path-only swap (no other content change)
      on an already-over-cap doc, then make the swap. Done-when: the stub file no longer exists and
      `python3 scripts/run_validators.py --scope all` stays green.
