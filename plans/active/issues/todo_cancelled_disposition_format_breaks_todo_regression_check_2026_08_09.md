---
doc_type: issue
title:
  "task_template.md's documented CANCELLED/SUPERSEDED non-checkbox disposition format conflicts with
  check_todo_regression.sh's literal checkbox-count invariant"
summary: >-
  `task_template.md` (the `/done`-time disposition markers section) documents converting a dead/re-scoped todo from `- [
  ] <brief>` to a bold non-checkbox bullet `- **[TAG] P<n>. CANCELLED — SUPERSEDED <date> (<who>, per <ref>).**`.
  `scripts/plan-hygiene/check_todo_regression.sh` independently enforces that a staged plan's TOTAL `^- \[[ xX]\]` count
  (open + done) never shrinks vs `origin/live-defi-rollout`, with no special-case for this exact, documented conversion
  — so following task_template.md's own convention hard-fails precommit as a false "todo loss." Found live 2026-08-09
  while cleaning up `uac_value_only_config_change_breaks_utl_untested_2026_07_20.md`'s two stale P2 items
  (struck-through SUPERSEDED/DO-NOT, previously left as bare `- [ ] [DEVOPS]` with no ingestion-gate marker) — attempted
  the documented CANCELLED conversion, `check_todo_regression (--only)` failed with `lost=2`. Worked around it by
  keeping the checkbox format and retagging `[DEVOPS]` -> `[OPERATOR]` instead (achieves the same
  backlog-ingestion-gating goal without the format conflict), but the underlying contradiction between the two docs is
  unresolved and will bite the next agent who follows task_template.md's own documented convention literally.
status: open
nature: issue
asset_group: [ci, ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ssot-contradiction, todo-format, quality-gates, plan-hygiene, findings-triage]
related:
  [/plans/active/task_template.md, /plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md]
created: 2026-08-09
author: unknown
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.2
assigned_role: devops
drift_direction: none
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "Found while recording a 2026-08-09 operator ruling on uac_value_only_config_change_breaks_utl_untested_2026_07_20.md
  and cleaning up that doc's todo-eligibility gaps before an assigned_vm: NA -> planning reclassification."
context_scope:
  [
    /plans/active/task_template.md,
    scripts/plan-hygiene/check_todo_regression.sh,
    /plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md,
  ]
---

# CANCELLED/SUPERSEDED disposition format vs `check_todo_regression.sh`

## What I found

`task_template.md`'s `/done`-time disposition markers section documents, verbatim:

> **`CANCELLED`/`SUPERSEDED`** — the todo is re-scoped or dead, nothing left to complete. Replace the `- [ ] <brief>`
> line with a bold, non-checkbox bullet: `- **[TAG] P<n>. CANCELLED — SUPERSEDED <date> (<who>, per <ref>).**`

`scripts/plan-hygiene/check_todo_regression.sh` counts `grep -cE "^- \[[ xX]\]"` (total open+done checkbox lines) per
staged plan and fails if the current total is less than `origin/live-defi-rollout`'s total for the same file — by
design, per its own header comment, this is meant to catch a genuine todo deletion/collapse, NOT a legitimate CANCELLED
conversion. The script has no special-case for the bold non-checkbox CANCELLED/SUPERSEDED bullet format — converting
even ONE stale `- [ ]` line to that format reads as a 1-todo "loss" and hard-fails the `--only` precommit check with
`LOSS <file> origin=N current=N-k lost=k`.

Live repro (2026-08-09): converted 2 stale struck-through P2 items in
`uac_value_only_config_change_breaks_utl_untested_2026_07_20.md` from
`- [ ] [DEVOPS] ~~...~~ **SUPERSEDED**`/`**DO NOT**` to the documented non-checkbox bold-bullet CANCELLED format.
`check_todo_regression (--only)` failed:
`LOSS uac_value_only_config_change_breaks_utl_untested_2026_07_20.md origin=7 current=5 lost=2`.

## Why it matters

An agent following `task_template.md`'s own documented convention literally, in good faith, hits a hard precommit
failure with a confusing message ("todo loss") that doesn't obviously point back to the CANCELLED-format conversion as
the cause — likely to cost real debugging time, or worse, get "fixed" by reverting to the (non-compliant, still
`- [ ]`-tagged) old format without anyone noticing the two docs disagree.

## Workaround used this session (not a fix)

Kept the checkbox format (`- [ ] [TAG] P<n>. ...`) and retagged `[TAG]` to `[OPERATOR]` instead of converting to the
bold non-checkbox bullet — achieves the same "keep it out of the AO backlog" goal via the `[OPERATOR]` ingestion-gate
marker family (`task_template.md`'s OTHER documented mechanism, the "Non-dispatchable" section) without touching the
checkbox count. This sidesteps the conflict but does not resolve it — the CANCELLED/SUPERSEDED format is still
documented as the correct mechanism in `task_template.md` and still not exempted by the checker.

## Todos

- [ ] [DEVOPS] P2. **Resolve the contradiction — pick one, then fix the other.** Either (a) teach
      `check_todo_regression.sh`'s `_check_one()` to recognize the CANCELLED/SUPERSEDED bold-bullet pattern (e.g. a line
      matching `^- \*\*\[[A-Z]+\] P\d\. CANCELLED`) and count it as equivalent to a retained checkbox line rather than a
      loss, or (b) update `task_template.md`'s CANCELLED/SUPERSEDED convention to keep the checkbox bracket
      (`- [ ] [TAG] P<n>. CANCELLED — SUPERSEDED ...`) instead of converting to a bold non-checkbox bullet, matching
      what `check_todo_regression.sh` already expects. Either fix is small; the risk is leaving them disagreeing.
      Done-when: a fresh conversion of a stale todo to CANCELLED/SUPERSEDED format, per whichever convention wins,
      passes `check_todo_regression.sh --only <file>` cleanly.
- [ ] [DOC] P3. Grep the corpus for any EXISTING bold non-checkbox `CANCELLED —`/`SUPERSEDED` bullets that may have
      already silently reduced a plan's checkbox total below its origin value without anyone noticing (this check only
      runs `--only` on STAGED files today, so a prior conversion that landed via a path that skipped this hook — e.g.
      `safe-doc-push.sh` before its own recent hardening, or a raw push — could be sitting unnoticed). Not urgent; a
      hygiene sweep item.

## Progress Log

- **2026-08-09**: Filed after hitting this live while cleaning up
  `uac_value_only_config_change_breaks_utl_untested_2026_07_20.md`'s two stale P2 items for AO-dispatch eligibility.
  Worked around it in that doc (kept checkbox format, retagged to `[OPERATOR]`) rather than force the CANCELLED
  conversion through; this doc tracks the real fix.
