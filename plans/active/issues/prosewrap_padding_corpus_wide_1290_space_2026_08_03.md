---
doc_type: issue
title:
  "Prettier proseWrap continuation-padding corruption is corpus-wide (82 docs, 4472 lines, up to 1290 leading spaces) —
  not the 2 instances the originating issue doc found"
summary: >-
  Root-causing prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md's P3 todo (reproduce + fix the proseWrap
  continuation-padding bug) surfaced that the corruption is far larger in scope than the 2 originally-flagged commits: a
  corpus-wide scan with the new scripts/plan-hygiene/check_prosewrap_padding.sh gate found 82 active plan/issue/codex
  docs already carrying this padding, 4472 violating lines total, up to 1290 leading spaces on one line
  (plans/active/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md — a content mirror of the doc that produced the
  original 2 flagged instances, reformatted many more times across subsequent unrelated commits). The new gate is now
  live (shrinking ratchet, baseline=4472) so this cannot grow further unnoticed, but the existing debt is untouched —
  that's this doc's scope.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [prettier, prosewrap, tooling, plan-hygiene, cosmetic, corpus-cleanup]
related: [/plans/archive/issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md]
created: 2026-08-03
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source:
  [
    "Discovered 2026-08-03 by slot 11 (backend_engineer) while root-causing
    prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md's first todo — a corpus-wide survey run as part of
    calibrating the new lint gate's threshold turned up far more existing damage than the 2 commits the parent issue doc
    named.",
  ]
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/archive/issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md,
    /scripts/plan-hygiene/check_prosewrap_padding.sh,
    /scripts/plan-hygiene/prosewrap_padding_baseline.yaml,
    /scripts/plan-hygiene/run_hygiene_sweep.sh,
  ]
---

# Prettier proseWrap continuation-padding corruption is corpus-wide

## What I found

While root-causing `prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md`'s first todo, I confirmed the bug
is a genuine, reproducible **prettier idempotency defect** (prettier 3.9.5 AND 3.9.6 — the latest release at
investigation time — both affected): a paragraph that is the 2nd+ block inside a list item, once it has been reflowed to
span multiple physical lines, gets its continuation lines' leading-space padding **increased on every subsequent
prettier pass over the same file** instead of converging to a stable wrap. Confirmed with a minimal 4-line fixture,
growing +4 spaces per pass (18→22→26→30→...) with **or without** any backtick inline-code span present — so despite the
parent issue doc's framing, this is not specifically about unbreakable inline-code tokens, it's a broader
list-item-continuation reflow bug. Full repro + minimization work is in the parent doc's Progress Log.

Building `scripts/plan-hygiene/check_prosewrap_padding.sh` (the fix for that todo) required calibrating a leading-indent
threshold against the live corpus, which meant scanning it — that scan found the corruption is NOT limited to the 2
commits the parent doc named:

- **82 files** across `plans/active/`, `plans/epics/`, and `codex/` carry at least one instance.
- **4472 total violating lines** (the gate's own count, now seeded as its ratchet baseline).
- The worst single instance: **1290 leading spaces** on lines 222-231 of
  `plans/active/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md` — this is the SAME paragraph that produced the
  original `tradfi_backfill_oom_remediation_2026_06_24.md` instances (18 spaces at first commit `e67a7367b`, 338 by
  `129905504`), mirrored into the satellite-batch doc and then reformatted across many MORE unrelated commits, each pass
  compounding the padding further.
- The full file list is reproducible on demand: `bash scripts/plan-hygiene/check_prosewrap_padding.sh` (no args = full
  default corpus scan) prints every file + flagged line.

## Why it matters

- Byte bloat + diff noise on 82 active docs — any future edit to one of these files carries this padding forward in
  `git diff`/`git blame` output, and (per the root-cause finding) makes it WORSE every time prettier reformats the file
  for an unrelated reason.
- The new gate (`check_prosewrap_padding.sh`, wired into `run_hygiene_sweep.sh`'s full sweep as a shrinking ratchet,
  same shape as `check_line_caps.sh` / `check_archive_candidates.sh`) stops this from growing unnoticed going forward,
  but does nothing about the existing 4472 lines — that debt needs a deliberate remediation pass, the same way
  `check_prettier_mangling.sh`'s corpus was fully repaired before that gate went live zero-tolerance (see
  `prettier_emphasis_mangling_corpus_corruption_2026_07_14.md`).

## Recommended decision

Mechanical, bounded remediation — not a design/judgment call:

1. Run `bash scripts/plan-hygiene/check_prosewrap_padding.sh` (no args) to get the current flagged file+line list.
2. Per flagged file: collapse each over-indented continuation line's leading whitespace back to the structurally-correct
   indent for its context (matching the list item's own body indent — usually 2/4/6 spaces depending on nesting depth),
   and collapse any 3+-space run found inside a backtick span back to a single space. Verify **content-only** via
   `git diff -w` (per the parent doc's own verification convention) before committing — this is pure whitespace repair,
   never a wording change.
3. Re-run `check_prosewrap_padding.sh --update-baseline` to lower the ratchet as files get fixed; the target is
   `violation_count: 0`.
4. Because prettier itself still has this idempotency bug (confirmed on latest 3.9.6), a REPAIRED file will drift again
   if it's touched by an unrelated commit and prettier-autostage reformats it — the gate (todo 2 below is NOT itself the
   fix, `check_prosewrap_padding.sh` is) will catch that recurrence going forward, but a repair pass alone doesn't make
   it permanent. No further action needed beyond keeping the gate live; re-open this doc if the ratchet baseline climbs
   again after remediation.

## Todos

- [ ] [BACKEND] P3. Batch-repair the leading-whitespace padding in the 82 flagged files (see § "What I found" — run
      `bash scripts/plan-hygiene/check_prosewrap_padding.sh` for the live list), collapsing over-indented continuation
      lines back to their structurally-correct indent and any 3+-space run inside a backtick span back to a single
      space. Verify content-only via `git diff -w` per file before committing. Fine to split across multiple
      commits/sessions — not a single-commit requirement. (repo: unified-trading-pm)
- [ ] [BACKEND] P3. Once the flagged-line count reaches 0 (or a deliberately-accepted lower plateau), run
      `check_prosewrap_padding.sh --update-baseline` to lower the ratchet from 4472 toward 0 and commit the updated
      `scripts/plan-hygiene/prosewrap_padding_baseline.yaml`. (repo: unified-trading-pm)

## Progress Log

- 2026-08-03 (slot 11, backend_engineer): filed while completing
  `prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md`'s first todo — the fix
  (`check_prosewrap_padding.sh`) required a corpus-wide calibration scan that surfaced this much larger existing-debt
  scope, which is out of that todo's bounded remit (reproduce + build the gate) and tracked here instead per the
  findings-closure rule. `assigned_vm: NA` per the ASK-BEFORE-CREATING default; operator/na-eligibility-audit can
  reclassify to `planning` if this precisely-scoped mechanical remediation should be AO-dispatched.

- **context-scout 2026-08-03**: populated context_scope (4 entries).
