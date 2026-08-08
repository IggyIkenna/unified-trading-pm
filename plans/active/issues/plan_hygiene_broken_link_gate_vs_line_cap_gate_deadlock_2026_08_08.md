---
doc_type: issue
title: >-
  Archiving any active/issues doc that a top-level plans/active/*.md links to via markdown syntax can permanently
  deadlock — the corpus-wide broken-link HARD gate and the line-cap HARD gate have no shared escape hatch
summary: >-
  Discovered live while archiving `provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md` (all 3
  todos done, immediate-archival HARD RULE per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`).
  `plans/active/cross_cutting_consolidated_closeout_2026_07_25.md` (1007L, already over the 1000L hard cap, `todos=1` so
  not itself archival-eligible) cites the doc via a markdown-syntax link
  `[...](/plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md)`. Once the
  target moves to `plans/archive/2026_08/issues/...`, that link 404s. `scripts/validators/validate_plan_links.py` (run
  unconditionally, corpus-wide, HARD, via `run_hygiene_sweep.sh`'s `--precommit` mode whenever a commit touches `plans/`
  or `codex/` — see `.pre-commit-config.yaml`'s `files: ^(plans/|codex/)` trigger) globs ALL of `plans/active/*.md` on
  every such commit regardless of what's staged, so this failure blocks EVERY future plans/codex-touching commit
  fleet-wide, not just the archival commit itself. Fixing the one-line link inside
  `cross_cutting_consolidated_closeout_2026_07_25.md` is the obvious fix, but that file is already 1007L (over the 1000L
  hard cap) and `check_line_caps.sh`'s ONLY carve-out for an over-cap file in SCOPED (pre-commit staged-file) mode
  requires the staged diff to have `DELETED=0` (a pure line-content substitution, e.g. swapping
  `/plans/active/issues/...` for `/plans/archive/2026_08/issues/...` within the same line, always produces `git diff
  --numstat` = `1 1` — one deleted line, one added line, never zero — because git diffs at line granularity, not
  character granularity). Live-verified: `sed -i 's#...#...#' cross_cutting_consolidated_closeout_2026_07_25.md` then
  `git diff --numstat -- <file>` → `1  1  ...` (confirmed, not assumed). No documented exception in either script covers
  "fix a stale outbound link in an over-cap file with a genuinely tiny (net-zero-length) edit." The archival ritual's
  own SSOT anticipates exactly this shape of conflict ("if the hook still blocks the staged move, that is the gate
  mis-scoping... fix the scoping, do not shrink a finished doc to appease it") but names no concrete fix.
status: open
nature: issue
asset_group: [ci, cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, line-caps, broken-links, archival, tooling-gap, pre-commit]
related:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-08
last_updated: "2026-08-08"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.25
assigned_role: infra
drift_direction: advance-process
depends_on: []
source:
  "cicd slot 6, discovered mid-archival of provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md,
  2026-08-08"
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    scripts/validators/validate_plan_links.py,
    scripts/plan-hygiene/check_line_caps.sh,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Broken-link gate vs. line-cap gate: no shared escape hatch for a stale outbound link in an over-cap doc

## What was found (live, 2026-08-08)

Attempting to archive `provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md` (all 3 todos `[x]`,
unlocked) per the immediate-archival HARD RULE:

1. `git mv` to `plans/archive/2026_08/issues/` + repointed 5 well-formed (leading-slash) active-corpus referrers —
   passed plan-hygiene cleanly for those.
2. `plans/active/cross_cutting_consolidated_closeout_2026_07_25.md` also cites the doc, but via markdown-link syntax
   `[`...`](/plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md)` (line
   741). Leaving it untouched → `validate_plan_links.py` (corpus-wide, unconditional, HARD) fails the commit:
   `BROKEN: active/cross_cutting_consolidated_closeout_2026_07_25.md -> /plans/active/issues/provenance_marker_…md`
   (the tool's own truncated error text — not a real path, quoted verbatim for evidence).
3. Fixing that one line → `check_line_caps.sh` SCOPED mode fails instead: the file is 1007L (over the 1000L hard cap,
   `todos=1` so not archival-eligible itself), and a same-line text substitution always shows `DELETED=1` in
   `git diff --cached --numstat` (verified directly, not assumed), which fails the ONLY over-cap carve-out
   (`DELETED=0 AND ADDED<=10 AND no added checkbox lines`).
4. No sequence of edits threads both needles at once for a plain link-repoint edit — the marker-append carve-out was
   designed for a small ADDITIVE Progress-Log/verdict marker, not a same-line link fix, and genuinely cannot express
   "replace this URL" as a zero-deletion diff.

**Why this is worse than a one-off**: `validate_plan_links.py --workspace-root` scans `plans/active/*.md`
unconditionally on every commit touching `plans/` or `codex/` (`.pre-commit-config.yaml`'s `files: ^(plans/|codex/)`
trigger) — this is NOT scoped to the staged files, so once ANY over-cap top-level plan carries a stale markdown link,
EVERY future plans/codex-touching commit fleet-wide fails until it's fixed, not just the one that broke it. This is a
standing corpus-wide commit-pipeline risk each time a doc gets archived out from under an over-cap referrer's markdown
link, not limited to this specific incident.

## Why not fixed autonomously here

Two options exist, both outside a P2 audit-task's scope to decide/implement unilaterally:

- **(a) Add a scoping fix to `check_line_caps.sh`**: extend the existing marker-append carve-out (or add a sibling one)
  to also permit a bounded, same-line URL/path substitution in an over-cap file — e.g. `ADDED<=DELETED` AND the diff's
  changed lines match only path-token differences, not new prose. This is a real code change to a shared pre-commit gate
  used fleet-wide; needs review, not a unilateral tweak mid-audit.
- **(b) Trim `cross_cutting_consolidated_closeout_2026_07_25.md`** below 1000L (a legitimate, separate maintenance task
  — it's 7L over) so the hard-cap branch never triggers for it. Requires reading the full 1007L doc and making a
  content-preserving judgment call about what's safely condensable; this is a different agent's active closeout tracker
  (`todos=1` still open), not something to touch as a side effect of an unrelated P2 audit.

Per this workspace's own precedent (`utl_ldr_main_blocked_34_foreign_quickmerge_bypasses_2026_07_21.md` and this doc's
own sibling `provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md`), a fix with fleet-wide tooling
blast radius is a human/operator decision, not an autonomous mid-task call — reverted the archival attempt cleanly
(working tree restored to match the already-landed `unified-trading-pm@9ec9cb1be` checkbox-flip commit) rather than
force it through or damage another agent's active doc.

## Options (operator decision)

- [ ] [OPERATOR] P1. Decide (a) extend `check_line_caps.sh`'s over-cap carve-out to cover a bounded link-repoint edit,
      or (b) authorize trimming `cross_cutting_consolidated_closeout_2026_07_25.md` under 1000L, or (c) some other
      resolution (e.g. a documented stub-redirect convention at the old path).
- [ ] [INFRA] P1. Once (a)/(b)/(c) is decided, implement it, THEN complete the deferred archival of
      `plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md` (all todos
      already `[x]`, unlocked, `resolved_by` ready to fill with the completing SHA) per the normal 6-step ritual.
