---
doc_type: issue
title: MOVED — see plans/archive/2026_08/issues/promote_ref_orphaned_on_manual_pr_close_2026_08_06.md
summary: >-
  Redirect stub. The underlying issue resolved and archived 2026-08-09 to
  `plans/archive/2026_08/issues/promote_ref_orphaned_on_manual_pr_close_2026_08_06.md`. This stub's own status is
  `blocked`, not `resolved` — it is NOT the resolved issue itself, it is a permanent-until-unblocked placeholder kept at
  the old path solely because `plans/active/cross_cutting_consolidated_closeout_2026_07_25.md` links this exact path.
  **STALE (corrected 2026-08-14, Item N):** the "already over the 1000-line hard cap" premise below no longer holds —
  the referrer is live-verified at 733 lines (split via an earlier, untraced commit; was 1007L when this stub was
  created), so `check_line_caps.sh`'s over-cap SCOPED-mode restriction does not apply to it anymore and a normal
  path-swap edit should now go through cleanly. Delete this stub once that referrer's line is repointed directly
  (tracked as a follow-up todo below) — the line-cap blocker that todo names is resolved; only the repoint+delete action
  itself remains outstanding.
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
`plans/active/cross_cutting_consolidated_closeout_2026_07_25.md`'s existing link to this path. **STALE (corrected
2026-08-14, Item N):** the claim that the referrer was "already over the `check_line_caps.sh` 1000-line hard cap" no
longer holds — live-verified 733 lines (well under cap), so a same-line path-swap no longer needs the SCOPED-mode
over-cap carve-out at all.

## Follow-up

- [ ] [DOCS] P3. Repoint `plans/active/cross_cutting_consolidated_closeout_2026_07_25.md`'s link for
      `promote_ref_orphaned_on_manual_pr_close_2026_08_06.md` from this stub path to
      `/plans/archive/2026_08/issues/promote_ref_orphaned_on_manual_pr_close_2026_08_06.md` directly, then delete this
      stub file. **The line-cap blocker this todo originally named is resolved (Item N, 2026-08-14) —
      `cross_cutting_consolidated_closeout_2026_07_25.md` is now 733 lines, under the 1000-line hard cap** — so this is
      now a plain, unblocked edit; only the repoint+delete action itself remains outstanding. Done-when: the stub file
      no longer exists and `python3 scripts/run_validators.py --scope all` stays green.

## Progress Log

- **context-scout 2026-08-09**: populated/refreshed context_scope (1 entry).
- **cross_cutting_satellite_ao_dispatch_batch13b Item N, 2026-08-14**: corrected the stale "already over the 1000-line
  hard cap" citation (summary + body) — live-verified `cross_cutting_consolidated_closeout_2026_07_25.md` is 733 lines.
  Text-only correction per Item N's scope (`plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md`);
  did not execute the Follow-up repoint+delete action itself (separately tracked above, now unblocked).
