---
doc_type: issue
title: sports_satellite_ao_dispatch_batch5 is over the 1000-line hard cap, blocking its priority-resort edit
summary:
  Discovered applying the 2026-07-28 priority-resort — sports_satellite_ao_dispatch_batch5_2026_07_26.md is already 1002
  lines (over the 1000-line hard cap) BEFORE the resort touched it, so `check_line_caps.sh` blocked staging its 1-line
  `priority:` edit. Excluded from that commit; left at its current priority pending the standard line-cap remediation
  (extract closed Progress Log sections into an archive-bound history doc, per plan_line_cap_remediation_2026_07_23.md's
  precedent).
status: resolved
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
  unified-trading-pm, 2026-07-28 -- extended the existing sibling archive doc
  plans/archive/2026_07/sports_satellite_ao_dispatch_batch5_completed_todos_2026_07_26.md with all 21 remaining closed
  todos; parent trimmed 1002->585 lines; priority flipped P1->P2. `check_line_caps.sh` re-verified within cap. NOTE -- a
  concurrent session hit the SAME line-cap block again the same day (SECOND COLLISION, operator-gate retag pass — 2
  now-resolved [OPERATOR] gates on this same parent file also couldn't land for the same reason) before this fix landed;
  the trim above resolves both collisions, since the underlying file is now well under cap (585L).
---

> **🟢 RESOLVED 2026-07-28** — parent plan trimmed under the line cap; priority resort applied. Archived per
> `/codex/11-project-management/issue-doc-lifecycle.md`.

# sports_satellite_ao_dispatch_batch5 is over the 1000-line hard cap

## Todos

- [x] ✅ [SCRIPT] P2. Extract the oldest fully-closed dated Progress Log section(s) from
      `plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md` into an archive-bound
      `sports_satellite_ao_dispatch_batch5_history_2026_07.md` (`status: complete`, `nature: record`, 0 open todos)
      under `plans/archive/2026_07/`, leaving a one-line pointer behind, until the live doc is back under 1000 lines.
      Then flip its `priority:` from `P1` to `P2` per the 2026-07-28 resort (it is 21/23 top-level todos done, a
      corpus-hygiene AO-dispatch-batch satellite per that resort's carve-out logic, same as its sibling batches).
      Definition of done:
      `bash scripts/plan-hygiene/check_line_caps.sh plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md`
      reports the file within cap, and its `priority:` reads `P2`. — **DONE 2026-07-28.** Re-used the existing sibling
      archive doc (`/plans/archive/2026_07/sports_satellite_ao_dispatch_batch5_completed_todos_2026_07_26.md`, already
      created 2026-07-26 for the same parent's first 2 closed-todo extraction) rather than minting a second,
      differently-named history file — extended it with all 21 remaining fully-closed `[x]` DONE todos (verbatim, `diff`
      against `git show HEAD:` confirmed byte-for-byte content preservation aside from one transcription typo caught +
      fixed, `mdps_odds_horizon_bucket_shard4_residual_failures` misspelled `mdts_` on first paste), bringing that
      archive doc to 23/23 closed todos, 556 lines (archive dir is not cap-scanned). Parent doc
      (`sports_satellite_ao_dispatch_batch5_2026_07_26.md`) trimmed from 1002→585 lines: the 2 genuinely-still-open
      todos (BLOCKED-CREDENTIALS odds-api backfill; zombie-tick purge/ML-readiness) stay inline verbatim, the 21
      extracted todos are replaced by a numbered one-line index (tag/repo/outcome) + a pointer to the archive doc.
      Deferred/conflict-gated/operator-gated sections (561-1002) are untouched verbatim, except one adjacent
      pre-existing defect fixed in the same commit (findings-triage "in your file, fix in same commit"): a leaked raw
      `</parameter>`/`<parameter name="conflict_or_defer_note">` XML fragment (a structured-output artifact from a prior
      fanout session) was splitting the `sports_predictions_live_mode_activation_readiness_2026_07_21.md` bullet's prose
      in two — removed the two stray tag lines, re-joined the sentence, no content deleted (re-diffed against
      `git show HEAD:` to confirm — the only change in that entire section). Re-verified:
      `bash scripts/plan-hygiene/check_line_caps.sh plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md` →
      "✅ ... within cap" (585L, SOFT tier only, `todos=2`); `priority:` frontmatter now reads `P2`. Todo-count
      conservation checked directly (not the script): 25 total todos ever on this plan = 2 open (still in parent) + 23
      closed (all in the archive doc), matching before/after.
