---
doc_type: issue
title:
  "M3's plan-flip verification is blind to a checkbox flip bundled with an archival git mv — blocks CLAUDE.md's own
  prescribed archival pattern"
summary: >-
  agent-orchestrator's `/done` M3 gate (`server/verify.py::check_plan_flip`) hard-rejects
  (`cross_repo_pm_file_touched_no_checkbox_flip`) any commit that flips a plan's checkbox to `[x]` in the SAME commit
  that `git mv`s the plan file to `plans/archive/`. This is exactly the archival pattern CLAUDE.md itself mandates
  ("this finalize doc itself gets archived alongside it in the same commit") — so the gate structurally cannot verify
  the standard, correct workflow for the final archival todo of every satellite-AO finalize plan.
status: open
resolved_by:
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, m3, plan-flip, verify, archival, gate-gap]
related:
  [
    /plans/archive/2026_07/tradfi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md,
    /plans/active/issues/defi_manifest_no_expected_unattempted_seeder_2026_07_26.md,
  ]
created: 2026-07-26
source:
  - "slot-11, 2026-07-26, hit while completing tradfi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md's archival
    todo (task_id tradfi_satellite_ao_dispatch_batch3_2026_07_26_finalize-003)"
assigned_vm: NA
assigned_role: general
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
drift_direction: advance-code
parent_epic: orchestrator_master
execution_scope: local-only
depends_on: []
locked_by:
---

# M3 plan-flip verification is blind to archival renames

## What I found

Completing `tradfi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md`'s last todo — the standard 6-step archival
ritual — I flipped the todo's `- [ ]` → `- [x]` AND `git mv`d both `tradfi_satellite_ao_dispatch_batch3_2026_07_26.md`
and its finalize doc from `plans/active/` to `plans/archive/2026_07/` **in the same commit**
(`unified-trading-pm@f8f9dc25b`), exactly matching CLAUDE.md's own archival-ritual wording: "this finalize doc itself
gets archived alongside it in the same commit."

`POST /api/slots/11/done` rejected it:

```json
{
  "detail": {
    "msg": "commit 'f8f9dc25b' does not touch the plan checkbox at 'plans/active/tradfi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md' — flip the checkbox ...",
    "plan_ref": "plans/active/tradfi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md",
    "reason": "cross_repo_pm_file_touched_no_checkbox_flip",
    "sha": "f8f9dc25b"
  }
}
```

**Root cause** — `server/verify.py::check_plan_flip` (agent-orchestrator):

1. Mode 1 (`plan_in_worker_tree`) requires `(resolved_worker / candidate).is_file()` for one of
   `_plan_ref_candidates(plan_ref)` — which only tries the literal `plan_ref` and its `issues/` variant
   (`_plan_ref_candidates`, lines 453-471). Neither exists post-rename, so mode 1 never engages.
2. Falls to mode 2 (cross-repo PM log walk). `_pm_log_commits_touching_plan_ref` finds the commit (a
   `git log -- <old_path>` DOES surface a commit that deletes/renames the path), but `_diff_flips_checkbox` then runs
   the equivalent of `git show <sha> -- <old_path>` — and confirmed live
   (`git show f8f9dc25b -- plans/active/ tradfi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md`), that diff is a
   **pure file deletion** (`deleted file mode 100644`, every line as `-`). The added `[x]`-flipped line only exists in
   the diff of the NEW path (`plans/archive/2026_07/...`), which the checker never looks at — git's default
   rename-similarity detection didn't kick in here because the edit (banner add, status flip, checkbox flip, ~40% of the
   file changed) dropped the path pair below git's default 50% similarity threshold for an implicit rename pairing in
   this diff mode.
3. `checkbox_flipped=False` → `todo_cancelled=False` (no CANCELLED marker was added, this was a real completion) → falls
   to `checkbox_currently_checked` fallback (line 845) — but that ALSO resolves via `_plan_ref_candidates`, which still
   doesn't know about the archive path, so `current_pm_text=None` and this fallback fails too. No path through the
   function succeeds for a genuine archive-rename+flip commit.

**Impact**: every satellite-AO batch's finalize plan ends with an archival todo worded almost identically to this one
(batch1/2/3-finalize precedent across tradfi/cefi/defi/sports/prediction/cross-cutting), each following the same
CLAUDE.md-prescribed "flip + archive in one commit" pattern. **Every one of those closing todos will hit this exact
409** when a worker follows the documented ritual correctly — the gate doesn't just miss an edge case, it structurally
cannot verify the standard, correct workflow for closing out any satellite-AO batch.

## Recommended fix (not attempted here — agent-orchestrator repo, out of scope for a data_engineering PM task)

Either: (a) `_plan_ref_candidates` should also try the plan's current location by resolving the rename via
`git log --follow --diff-filter=R -- <old_path>` (or checking `verified_files` for an add at a
`plans/archive/**/ <basename>` path with the same basename) and diff THAT path instead; or (b) when the old-path diff is
a pure deletion, fall back to diffing the corresponding added path in the same commit (matched by basename) before
declaring `file_touched_no_checkbox_flip`.

## What I did instead

Same precedent as `defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`'s slot-2 entry, `BLK-0222fc53`.

Self-`/skip-current-task` on `tradfi_satellite_ao_dispatch_batch3_2026_07_26_finalize-003` rather than repeatedly
retrying a `/done` call that cannot structurally succeed — the actual archival work is genuinely complete and pushed
(`unified-trading-pm@f8f9dc25b`, verified live: both docs at `plans/archive/2026_07/`, checkbox `[x]`, all 8 corpus
referrers fixed). No further action needed on the PM side; this doc tracks the agent-orchestrator-side gate fix as its
own independently-scoped follow-up.
