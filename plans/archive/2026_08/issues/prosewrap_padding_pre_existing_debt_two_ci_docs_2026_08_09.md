---
doc_type: issue
title:
  Two ci-tranche issue docs carry severe pre-existing prosewrap-padding corruption (880+ leading spaces) that blocks any
  future edit's prek commit
summary: >-
  While archiving `ci_satellite_ao_dispatch_batch1_2026_07_26.md` (finalize todo 4), repointing a one-line corpus
  reference in `plans/active/issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md` and
  `plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md` tripped
  `check_prosewrap_padding.sh`'s `--only` precommit hook — both files already carry, at HEAD, continuation lines with
  ~880-900 leading space characters (confirmed via direct Python inspection, not a rendering artifact). This is the same
  root-cause class as `plans/archive/issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md` (already
  resolved/archived there) — prettier's proseWrap reflow is not idempotent on this content, so re-staging either file
  (for ANY reason, not just this session's edit) produces a slightly different padding amount each time, which the
  `--only` HEAD-vs-staged signature diff flags as a "new" violation and blocks the commit. Left both files untouched
  this session (reverted the intended one-line path repoint in each) rather than risk a bulk regex fix on unrelated,
  severely mangled content; `check_reference_paths.py`'s corpus-wide existence count stays within its shrinking-ratchet
  baseline either way (measured 82 vs baseline 86 with these 2 left un-repointed).
status: resolved
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci, prettier, prosewrap, plan-hygiene, precommit]
related:
  [
    /plans/archive/issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: cicd
author: slot 18
source: ["plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md"]
resolved_by: unified-trading-pm@b8847a8a2
locked_by:
drift_direction: advance-code
depends_on: []
---

> **ARCHIVED 2026-08-09** — both todos hand-repaired (91 over-padded continuation lines collapsed to sane indentation in
> `uac_value_only_config_change_breaks_utl_untested_2026_07_20.md`, 27 in
> `silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md`); `check_prosewrap_padding.sh --only` passes clean
> on both files; content-only verified via `git diff -w` (empty) on each. See the Progress Log below for the shipped
> commits.

## What I found

Two `plans/active/issues/*.md` docs already carry, at their committed HEAD content (not introduced this session),
continuation lines with 880-900+ leading space characters:

- `plans/active/issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md` — 27 flagged lines (indent
  widths 774/776/890 chars) around lines 117-155.
- `plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md` — 61 flagged lines (indent width
  26+ chars at the smaller end, worse elsewhere) starting around line 26.

Verified via direct Python inspection (`len(line) - len(line.lstrip(' '))`) — not a terminal/tool rendering artifact.
`check_prosewrap_padding.sh --only <file>` flags both as carrying a "NEW" violation the moment either is staged for ANY
reason, because prettier's proseWrap reflow is not byte-stable on this content (confirmed: HEAD had 882 leading spaces
on one flagged line; after this session's prettier autostage pass it became 890 — a different amount, which the
HEAD-vs-staged signature diff reads as new content even though the underlying padding bug is old).

## Why it matters

Any future worker who needs to make even a trivial edit to either file (e.g. the next corpus-wide reference-path
migration, or fixing a stale citation) will hit the same precommit block this session did, unless they know to
exclude/pre-repair the file first. This is a landmine, not a one-off.

## Recommended decision

Apply the same fix pattern `prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md`'s todo 2 already used for
`sports_stats_delayed_live_capture_still_dead_post_fix_2026_07_29.md` (`unified-trading-pm@fd1b02c2c`): hand-repair by
collapsing the over-padded continuation lines back to sane indentation, verify content-only via `git diff -w` (zero
semantic change), confirm `check_prosewrap_padding.sh` passes clean afterward, ship via `quickmerge --agent --files` or
`safe-doc-push.sh`.

## Todos

- [x] ✅ [BACKEND] P3. Hand-repair the ~27 over-padded continuation lines in
      `silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md` (lines ~117-155), collapsing each flagged
      line's leading-whitespace run to sane indentation. Verify content-only via `git diff -w` (zero semantic change)
      before shipping. **Done when**: `check_prosewrap_padding.sh --only <path>` passes clean on that file. (repo:
      unified-trading-pm)
- [x] ✅ [BACKEND] P3. Hand-repair the ~61 over-padded continuation lines in
      `uac_value_only_config_change_breaks_utl_untested_2026_07_20.md` (starting ~line 26), collapsing each flagged
      line's leading-whitespace run to sane indentation. Verify content-only via `git diff -w` (zero semantic change)
      before shipping. **Done when**: `check_prosewrap_padding.sh --only <path>` passes clean on that file. (repo:
      unified-trading-pm)

## Progress Log

- **2026-08-09 (slot 18)** — Filed while archiving `ci_satellite_ao_dispatch_batch1_2026_07_26.md` (finalize todo 4):
  the archival's corpus-referrer repoint step hit this precommit block on these 2 files and deferred them rather than
  risk a bulk fix mid-archival. `check_reference_paths.py` confirmed within baseline either way (not a blocking
  regression from leaving these 2 un-repointed).
- **2026-08-09 (slot 28, backend_engineer) — todo 1 DONE**: hand-repaired all 27 over-padded continuation lines in
  `silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md` (lines 117-125, 127-132, 151-160, 162-163 —
  894/778/780 leading spaces collapsed to the sibling-line convention of 6). Verified content-only via `git diff -w`
  (empty output) and zero remaining lines with >=14 leading spaces in the file. `check_prosewrap_padding.sh --only`
  passes clean. Todo 2 (`uac_value_only_config_change_breaks_utl_untested_2026_07_20.md`) left untouched — out of this
  task's dispatched scope.
- **2026-08-09 (slot 30, backend_engineer) — todo 2 DONE**: hand-repaired all 91 over-padded continuation lines in
  `uac_value_only_config_change_breaks_utl_untested_2026_07_20.md` (2 blocks: lines 232-325 and 367-378 at the time of
  the fix — over-indented at 30/46 leading spaces vs the sibling checkbox-continuation convention of 6; count grew from
  the issue doc's originally-cited ~61 to 91 due to further intervening prettier passes on this doc between filing and
  this fix). Collapsed each flagged line's leading-whitespace run to 6 spaces (matching adjacent unaffected continuation
  lines in the same list items). Verified content-only via `git diff -w` (empty output) and 0 remaining lines with >=14
  leading spaces. `check_prosewrap_padding.sh --only <path>` passes clean. Both todos now closed; this issue doc is now
  archival-eligible. Set `archive_exempt: true` on this flip-only commit per the documented two-commit bridge
  (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § "archive_exempt: true is the sanctioned
  bridge") — the immediately-following `git mv` archival commit drops the field.
