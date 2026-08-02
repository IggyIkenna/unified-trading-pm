---
doc_type: issue
title:
  "AO /done M3 tag-correlation fallback false-matched an unrelated checked todo when a checkbox is retagged with a
  leading BLOCKED-<TOKEN> marker"
summary: >-
  agent-orchestrator/server/verify.py's `_brief_is_checked_by_tag_in_text` (the M3 plan-flip verification's
  tag+priority-correlated fallback) requires a task's `brief` string to start with the exact `[TAG] P<n>.` prefix
  (`_TODO_TAG_PRIORITY_RE = re.compile(r"^\[(.+?)\]\s+P(\d+)\.")`). When a checkbox is retagged with a marker placed
  BEFORE the tag (e.g. `- [ ] BLOCKED-UPSTREAM-DESIGN [DATA] P2. ...` — the convention slot-12 used, non-standard vs.
  this corpus's usual marker-AFTER-tag placement), two independent bugs surface: (1) for the ORIGINAL pre-retag task,
  the fallback spuriously correlates against ANY OTHER checked `[x] [TAG] P<n>.` line sharing the same tag+priority
  anywhere in the doc, even if it's a completely unrelated todo — confirmed live: task
  `canonical_path_oracle_blind_to_filename_stem-002`'s `/done` (slot-12, `unified-trading-pm@5f00baeed`, retag-only
  commit, checkbox correctly left `[ ]`) was accepted as `checkbox_checked_tag_correlated` solely because the SAME doc
  has an unrelated `- [x] [DATA] P2. Decide the id grammar for defi...` line at L304 sharing the `[DATA] P2.` prefix — a
  false-positive completion signal, not a real correlation to THIS todo. (2) for the NEXT regen'd task off the SAME
  already-retagged checkbox, the fallback (and its `_marker_disposition_in_text` sibling) can never fire AT ALL, because
  the newly-dispatched task's OWN `brief` now starts with `BLOCKED-UPSTREAM-DESIGN ` (not `[DATA]`), breaking
  `_TODO_TAG_PRIORITY_RE`'s leading-anchor match — confirmed live: task
  `canonical_path_oracle_blind_to_filename_stem-003` (slot-6) hit a hard `409
  cross_repo_pm_file_touched_no_checkbox_flip` on this same checkbox despite the underlying disposition being identical
  (still gated, still correctly unflipped) to -002's accepted case. No plan-doc edit can fix case (2) — `brief` is
  captured at dispatch time, not re-read from the doc.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [ao-server, m3-verification, done-gate, tag-correlation, false-positive, regen-churn]
related: [canonical_path_oracle_blind_to_filename_stem_2026_07_20]
created: 2026-08-02
author: slot-6
assigned_vm: planning
execution_scope: ao-dispatched
priority: P2
parent_epic: agent_operating_framework_master
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: infra
drift_direction: none
source: [worker-session]
resolved_by:
locked_by:
---

# AO `/done` M3 tag-correlation fallback: false-match + leading-marker blind spot

## What I found

While closing `canonical_path_oracle_blind_to_filename_stem_2026_07_20.md`'s §7 "quarantine/honest-absence disposition"
todo's redispatch churn (separately fixed: `agent-orchestrator@2b0b9e9` added `UPSTREAM-DESIGN` to
`regen_backlog_from_plan.py`'s `_BLOCKED_TOKEN_RE` so the checkbox stops re-entering the backlog), I hit a
`409 cross_repo_pm_file_touched_no_checkbox_flip` on `/done` for task `canonical_path_oracle_blind_to_filename_stem-003`
even though the checkbox is legitimately, deliberately staying `[ ]` (same disposition slot-12's predecessor task `-002`
was accepted for minutes earlier).

Root-caused via `server/verify.py`'s `_brief_is_checked_by_tag_in_text` / `_marker_disposition_in_text`, both gated on
`_TODO_TAG_PRIORITY_RE.match(brief.strip())` matching `brief`'s LEADING characters against `^\[TAG\]\s+P<n>\.`:

- Task `-002`'s `brief` was captured pre-retag:
  `"[DATA] P2. The legitimately-unresolvable objects need a quarantine / honest-absence disposition (separate design)."`
  — starts cleanly with `[DATA]`, so the tag+priority extraction succeeds (`tag="DATA", priority="2"`). The fallback
  then scans the CURRENT doc for any `- [x] [DATA] P2. ...` line — finds exactly one, at L304
  (`"Decide the id grammar for defi..."`, a fully unrelated, genuinely-completed todo) — and reports `hits==1` →
  `checkbox_checked_tag_correlated: True`. This is WRONG: it correlated task -002 to a different todo's completion, not
  evidence that -002's own line changed state.
- Task `-003`'s `brief` was captured post-retag:
  `"BLOCKED-UPSTREAM-DESIGN [DATA] P2. The legitimately-unresolvable objects need a quarantine / honest-absence"` — the
  leading `BLOCKED-UPSTREAM-DESIGN ` token breaks `_TODO_TAG_PRIORITY_RE`'s anchor, so `m` is `None` and the fallback
  returns `(False, False, False)` / `False` immediately, regardless of anything in the doc. Every diff-based check
  (`_diff_flips_checkbox`, `_diff_blocks_checkbox`, etc.) also legitimately fails (the commit that ships the durable fix
  touches a DIFFERENT repo — `agent-orchestrator` — and the PM commit in the same session only appended a Progress Log
  entry, correctly not re-touching the already-retagged checkbox line). Net: a `409`, un-resolvable by any plan-doc
  edit, since `brief` is fixed at dispatch time.

## Why it matters

- **False positive (case 1)** silently accepts a `/done` whose cited commit did NOT actually establish the claimed
  disposition for THAT todo — exactly the failure class `ao_backlog_regen_integrity_2026_07_20.md`'s "checkbox state =
  truth" principle exists to prevent, via an accidental same-tag-priority collision the tag-correlation fallback wasn't
  designed to guard against for this direction (it already fails CLOSED on >1 hit — this is 1 hit, but the WRONG line).
- **False negative (case 2)** blocks a legitimate `/done` for a todo whose disposition is genuinely, correctly unflipped
  — forcing the worker into `/skip-current-task` (this session's resolution) even when real, valuable, shipped work was
  done. Every FUTURE todo retagged with a leading `BLOCKED-<TOKEN>` marker (an increasingly common convention —
  `ao_residuals_after_dispatch_hardening_2026_07_17.md`, `ao_open_issues_consolidated_close_out_2026_07_17.md` use the
  same leading-marker placement) will hit this identical wall.

## Recommended decision

Not a judgment call — this is a mechanical fix to `agent-orchestrator/server/verify.py`, but not one to speculatively
widen without care (loosening `_TODO_TAG_PRIORITY_RE` to tolerate a leading marker would also widen case (1)'s
false-positive surface). Recommend, in order:

1. Fix `_TODO_TAG_PRIORITY_RE` to optionally skip a leading `BLOCKED-[A-Z-]+\s+` / `CANCELLED\s+` / etc. token before
   anchoring on `[TAG] P<n>.` — closes the case-2 blind spot for the (now-common) leading-marker convention.
2. Separately harden `_brief_is_checked_by_tag_in_text` / `_marker_disposition_in_text` against case-1's false positive:
   correlate on a snippet of `brief`'s OWN distinguishing text (not just tag+priority) when more than one
   same-tag-priority line exists in EITHER state (checked or marker) — or, simpler, additionally require the
   checked/marker line's TEXT to share some non-trivial substring with `brief` beyond the shared tag+priority prefix,
   since tag+priority alone is not unique across a doc (this issue doc alone has 6+ `P2.` todos).
3. Add regression tests mirroring both live cases above (same-tag-priority collision against an unrelated checked line;
   a `brief` with a leading BLOCKED-<TOKEN> marker).

## Todos

- [ ] [INFRA] P2. Widen `_TODO_TAG_PRIORITY_RE` (or add a preprocessing strip) so a `brief`/plan line with a leading
      `BLOCKED-<TOKEN>` (or similar) marker before `[TAG] P<n>.` still extracts tag+priority correctly. Add a regression
      test using a brief like `"BLOCKED-UPSTREAM-DESIGN [DATA] P2. ..."`. (repo: agent-orchestrator)
- [ ] [INFRA] P2. Harden `_brief_is_checked_by_tag_in_text` (and `_marker_disposition_in_text`'s analogous risk) against
      correlating to an UNRELATED same-tag-priority line — require some shared distinguishing text beyond the
      tag+priority prefix, or otherwise prove the matched line actually corresponds to `brief`'s todo. Add a regression
      test mirroring the live L304/`canonical_path_oracle_blind_to_filename_stem-002` false-positive (two different
      `[DATA] P2.` todos in one doc, only one checked, brief belongs to the OTHER one). (repo: agent-orchestrator)

## Progress Log

- **slot-6 2026-08-02**: filed after hitting the case-2 blind spot closing
  `canonical_path_oracle_blind_to_filename_stem-003`; empirically reproduced case-1's false positive by re-running
  `verify.check_plan_flip` against slot-12's real `unified-trading-pm@5f00baeed` commit. Resolved my own session via
  `/skip-current-task` (task correctly stays un-completable via `/done` as scoped; the substantive churn-fix is already
  shipped and logged in `canonical_path_oracle_blind_to_filename_stem_2026_07_20.md`'s Progress Log).
