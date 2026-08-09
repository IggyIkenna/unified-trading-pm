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
  `git diff --numstat -- <file>` → `1 1 ...` (confirmed, not assumed). No documented exception in either script covers
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
   `BROKEN: active/cross_cutting_consolidated_closeout_2026_07_25.md -> /plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md`
   (once archived out from under this path).
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

- [x] ✅ [DOC] P1. **RULED 2026-08-09 (operator, via main session):** option **(a)** — extend `check_line_caps.sh`'s
      over-cap carve-out to also permit a bounded same-line link-repoint edit (`ADDED<=DELETED`, every changed line
      differing only by a `/plans/active/...`→`/plans/archive/...` path-token substitution, no new prose) alongside the
      existing marker-append carve-out. Retagged from `[OPERATOR]` in the same edit the ruling landed.
- [x] ✅ [INFRA] P1. **Implemented 2026-08-09** — `unified-trading-pm@d765b4cfb1` (shipped via
      `scripts/quickmerge.sh --agent --files`). Added a second SCOPED-mode carve-out to `check_line_caps.sh`: allowed
      when (a) the file is already over cap before this commit, (b) the staged diff's `ADDED<=DELETED`, and (c) every
      changed (+/-) content line, after normalizing an `/plans/active/...` or `/plans/archive/<YYYY_MM>/...` path
      segment to a common token, is textually identical between the removed and added sides. Verified via an isolated
      scratch git repo (not the real corpus, to avoid touching any live doc mid-audit): the exact real-world scenario
      from this doc's own "What was found" section (a `sed`-style same-line link-repoint on a 1001L over-cap doc,
      `git diff --numstat` = `1 1`) now passes as `SOFT` instead of `HARD`; confirmed the carve-out does NOT over-permit
      — a sneaky same-line prose addition alongside the path fix, and a file newly crossing the cap in the same commit,
      both still correctly fail `HARD`. **Deliberately NOT done in this same pass: completing the deferred archival of
      `provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md`.** That doc's own
      `archive_exempt: true` banner (set 2026-08-09) names this exact fix as the unblocking condition, but
      completing the archival for real also requires a corpus-wide referrer-path fixup across **11 active-corpus files**
      (`cross_cutting_consolidated_closeout_2026_07_25.md` — the one that triggered this deadlock — plus
      `ao_satellite_ao_dispatch_batch12_2026_08_09.md`, `ag_closeout_audit_cross_cutting_parked_2026_08_07.md`,
      `ag_closeout_audit_cross_cutting_parked_2026_08_08.md`,
      `assigned_role_devops_invalid_value_corpus_wide_2026_08_08.md`, `host_root_disk_full_transient_2026_07_13.md`,
      `governance_sweep_deferred_followups_2026_08_06.md`,
      `workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md`,
      `ao_scheduled_job_reserve_and_staggering_2026_08_04.md`,
      `semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md` (2 refs), `/codex/08-workflows/ci-cd-flow.md`) —
      a materially larger, separately-scoped unit of work than "implement the carve-out," and this issue's own scope
      (per the task that ruled it) was the carve-out itself. Left as its own explicit next todo below rather than
      silently expanding scope mid-fix.
- [ ] [INFRA] P1. **Complete the deferred archival** of
      `plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md` (all 3 todos
      already `[x]`, unlocked, `archive_exempt: true` pending exactly this) now that the carve-out fix above is shipped
      and verified: `git mv` to `plans/archive/2026_08/issues/`, repoint the 11 active-corpus referrers enumerated above
      (the `check_line_caps.sh` fix unblocks `cross_cutting_consolidated_closeout_2026_07_25.md`'s specifically — the
      other 10 aren't over-cap and don't need the carve-out, just a normal link update), un-set `archive_exempt`, fill
      `resolved_by` with the completing SHA, run the standard 6-step archival ritual.

## Progress Log

- **2026-08-08, filed**: discovered live while archiving
  `provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md`; reverted the archival attempt cleanly
  rather than force a fleet-wide tooling change mid-audit. See "Why not fixed autonomously here" above.
- **2026-08-09 (operator ruling batch, this session)**: Operator ruled option (a). Implemented + shipped
  `unified-trading-pm@d765b4cfb1` (quickmerge, code change to `scripts/plan-hygiene/check_line_caps.sh`). Verified
  against the exact real scenario in an isolated scratch repo (never touched the live corpus mid-verification) plus 2
  negative cases (sneaky prose, newly-crossing-cap file) to confirm the carve-out is bounded, not over-permissive. Did
  NOT complete the actual deferred archival in this same pass — that requires a separate 11-file referrer fixup, left as
  its own explicit todo above. Also updated the sibling doc
  `ao_dispatch_ignores_same_doc_operator_predecessor_todo_2026_08_08.md`'s `[OPERATOR]` todo to reflect this ruling
  landing (its own park/unpark mechanism is a live-AO-state action outside this doc-editing session's reach — noted
  there as a standing follow-up).
