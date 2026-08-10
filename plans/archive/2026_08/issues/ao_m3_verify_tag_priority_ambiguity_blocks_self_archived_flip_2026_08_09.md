---
doc_type: issue
title:
  agent-orchestrator's cross-repo M3 `/done` verification (`server/verify.py`) false-negatives on a self-archived
  checkbox flip when a doc has 2+ todos sharing the same `[TAG] P<n>.` prefix, both closed in the same commit as the
  doc's own archival `git mv`
summary: >-
  Live-observed 2026-08-09 finishing `blocked_queue_unanswered_questions_pruned_without_resolution-c7aae019dec9` (plan
  `plans/archive/2026_08/issues/blocked_queue_unanswered_questions_pruned_without_resolution_2026_08_08.md`).
  `check_archive_candidates.sh`'s `--only` precommit mode fires unconditionally once a staged doc has 0 open todos +
  some done + unlocked (regardless of `status:`), which forces the checkbox flip and the archival `git mv` into ONE
  commit instead of the two-commit sequence `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`
  prescribes ("never combine the checkbox flip with the git mv archival in ONE commit"). That combined commit's `/done`
  M3 check then rejected with `cross_repo_pm_file_touched_no_checkbox_flip` even though the flip genuinely happened:
  `verify.py`'s diff-based checks (`_diff_flips_checkbox`/`_flips_at_path_or_rename`) see a pure delete-at-old-path +
  pure-add-at-new-path (plain `git show -- <path>` doesn't pair the rename without `-M`, so neither side's diff has both
  a removed unchecked line AND an added checked line), and both content-based fallbacks also failed:
  `_brief_is_currently_checked` requires an EXACT single-line match against the task's `brief` string, which the
  workspace's own mandatory `✅` decoration (CLAUDE.md's commit-push-flip convention) breaks by design;
  `_brief_is_checked_by_tag_in_text` requires EXACTLY ONE `[TAG] P<n>.`-checked line in the destination text, and this
  doc had TWO `[BACKEND] P1.` todos both closed by the same commit — ambiguous, fails closed (by design, per that
  function's own docstring, to avoid a false-positive match on the WRONG todo). Worked around live by retagging one todo
  `[BACKEND]` → `[REVIEW]` (a legitimate correction — that todo shipped no code, investigation-only) which incidentally
  resolved the ambiguity, but that fix only works when one of the colliding todos happens to be mis-tagged; a doc with
  two genuinely-identical `[TAG] P<n>.` todos (e.g. two real `[BACKEND] P1.` code-change todos) would have no such
  escape hatch.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, verify, done-gate, m3, archival, plan-hygiene]
related:
  [
    /plans/archive/2026_08/issues/blocked_queue_unanswered_questions_pruned_without_resolution_2026_08_08.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: 2026-08-09
author: backend_engineer worker slot-18
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
drift_direction: NA
source:
  backend_engineer worker slot-18, 2026-08-09, discovered while archiving
  blocked_queue_unanswered_questions_pruned_without_resolution_2026_08_08.md as its last todo's own `/done` call.
resolved_by:
depends_on: []
locked_by:
context_scope:
  [agent-orchestrator/server/verify.py, /codex/12-agent-workflow/plan-completion-and-archival-discipline.md]
---

> **ARCHIVED 2026-08-09** — resolved: `_archival_rename_disposition` now falls through to an ordinal-position
> correlation (`_disposition_by_tag_position`) when content correlation is ambiguous. See the Todo/Progress Log below
> for the shipped commit and the reasoning for implementing Option (b) instead of the originally-recommended Option (a).
> No corpus referrers to this doc were found at archive time.

## What I found

`agent-orchestrator/server/verify.py`'s cross-repo M3 disposition chain (`_mode2_disposition`) tries, in order: a
diff-based checkbox flip at the literal path or its same-commit rename (`_flips_at_path_or_rename` and its
CANCELLED/DEFERRED/BLOCKED siblings), then `_archival_rename_disposition` (content-based, tag+priority-correlated). None
of these can confirm a real flip when BOTH of the following are true in the same commit:

1. The doc's own archival `git mv` bundles with the checkbox flip (the hygiene-enforced shape — see "Why it matters"
   below for why this is not optional), so the destination path's diff is a pure git "add" with no removed line to
   correlate against a diff-based check.
2. The doc has 2+ todos sharing the same `[TAG] P<n>.` prefix that are ALL checked as of that commit —
   `_brief_is_checked_by_tag_in_text` (the fallback `_archival_rename_disposition` relies on) requires
   `len(matches) == 1` and fails closed otherwise (by design, to avoid a false-positive on the wrong todo — see its
   docstring citing `ao_done_gate_tag_correlation_false_match_on_leading_marker_2026_08_02.md`).

The remaining fallback, `_brief_is_currently_checked` (exact single-line match against the raw `brief` string), also
structurally cannot help: the workspace's own mandated flip format (CLAUDE.md's commit-push-flip HARD RULE) appends a
`✅` immediately after `[x]`, and `_brief_is_currently_checked` has no tolerance for that decoration (unlike its
tag-correlated sibling, which explicitly documents tolerating it).

## Why it matters

The two-commit sequence (flip first, `git mv` second) that would avoid this entirely is exactly what
`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` already prescribes — but
`check_archive_candidates.sh --only` (precommit-scoped mode, added 2026-08-09) fires on the FIRST commit alone (a doc
with 0 open todos + some done + unlocked, sitting in `plans/active/`, regardless of `status:`), before the second
`git mv` commit can land. A worker following the archival-discipline SSOT to the letter is precommit-blocked from doing
so; a worker who bundles the two commits into one (the only way past the hygiene gate) then fails the `/done` M3 check
on any doc with a `[TAG] P<n>.` collision among its own todos. Confirmed live: exactly this sequence on
`blocked_queue_unanswered_questions_pruned_without_resolution_2026_08_08.md` (two `[BACKEND] P1.` todos, both closed by
the archival commit) — recovered only because todo 1 happened to be mis-taggable to `[REVIEW]` (investigation-only, no
code shipped). A doc where both colliding todos are genuinely, correctly the same tag+priority has no such escape.

## Recommended decision

Either (a) teach the two archival-adjacent checks in `verify.py` to re-run their rename-pairing diffs with `-M` (so
`git show -M <sha> -- <old_path>`/`<new_path>` pairs the rename and shows the real content delta, letting the existing
diff-based `_diff_flips_checkbox` succeed directly without needing the weaker content-based fallbacks at all), or (b)
extend `_archival_rename_disposition`'s ambiguity handling to disambiguate multiple same-tag-priority matches by ALSO
requiring the destination line to be new/changed relative to the PARENT revision at the archived path's PRE-rename
content (i.e., only count a checked `[TAG] P<n>.` line as a candidate match if its parent-revision counterpart — matched
by relative position/order within the todo list — was NOT already checked), rather than failing closed on any count > 1.
Option (a) is the more general fix (also closes the `_diff_flips_checkbox` pure-delete/pure-add gap directly,
independent of tag ambiguity).

## Todo

- [x] ✅ [BACKEND] P2. In `agent-orchestrator/server/verify.py`, fix `_flips_at_path_or_rename` (and its
      CANCELLED/DEFERRED/BLOCKED siblings) to re-invoke their underlying `git show` calls with `-M` (rename detection)
      when the literal-path diff is a pure delete, so a same-commit archival `git mv` bundled with a real checkbox flip
      is detected directly via the diff (not only via the weaker `_archival_rename_disposition` content-based fallback
      that fails closed on a `[TAG] P<n>.` collision). Add a regression test: two todos sharing the same `[TAG] P<n>.`
      prefix, both flipped `[x]` in the SAME commit that also `git mv`s the doc to `plans/archive/<YYYY_MM>/`, must
      resolve `checkbox_flipped=True` for either todo's `brief`. (repo: agent-orchestrator) —
      agent-orchestrator@2dccb9f4a

## Progress Log

- 2026-08-09 (slot 18, backend_engineer): Filed during the same session that hit this gap live — see the referenced
  archived doc's Progress Log for the full blow-by-blow (retag workaround, exact function-level root cause). Not fixing
  inline in this session (out of scope for the task that surfaced it; this doc tracks the fix as its own bounded,
  AO-eligible unit).
- 2026-08-09 (slot 24, backend_engineer): Implemented **Option (b)** from the "Recommended decision" above rather than
  the literal `-M`-on-`git show` mechanism the todo described. Traced through Option (a): passing both pathspecs to one
  `git show` (with or without `-M`) makes `_flips_at_path_or_rename` scan the WHOLE old+new file pair as one diff, which
  reliably closes the gap for a single-todo doc but produces false positives on a doc with 2+ todos where only the LAST
  one closes in the archival commit and the others were already `[x]` in an earlier commit — those already-checked lines
  show as "added" too (pure-add diff), so `added_checked_line` goes true regardless of which todo the removed line was.
  It would also change the resolution path (and `reason`) for the two ALREADY-PASSING tests
  `test_done_accepts_cross_repo_self_archived_with_annotated_checked_line` and
  `test_done_rejects_cross_repo_self_archived_ambiguous_tag_priority` (the latter would flip from reject to accept).
  Option (b) — ordinal-position correlation between the parent and destination revisions
  (`_disposition_by_tag_position`/`_tag_priority_line_statuses`) — avoids both problems: it doesn't touch
  `_flips_at_path_or_rename` at all, so every existing test's behavior is unchanged (verified: full existing suite green
  including the two tests above), and it resolves the new regression test's two-genuinely-different-todos-sharing-a-
  tag+priority-and-vocabulary case cleanly. `quality-gates.sh` full run green (2913 passed); shipped
  agent-orchestrator@2dccb9f4a.
