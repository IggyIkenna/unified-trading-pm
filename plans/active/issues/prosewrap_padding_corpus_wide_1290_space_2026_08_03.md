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
related:
  [
    /plans/archive/issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-03
author: unknown
parent_epic: infrastructure_master
assigned_vm: planning # reclassified NA -> planning 2026-08-03 (na-eligibility-audit, cross-cutting tranche) — conflict-check CLEAR
execution_scope: orchestrator-agent
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
      commits/sessions — not a single-commit requirement. **Automation available (2026-08-10, 18th promote-wall dispatch
      agt-e56165): `scripts/plan-hygiene/fix_prosewrap_padding.py` automates exactly this repair for a given set of
      files — run it on the live-flagged list, then verify with the gate. Read its docstring first (it encodes the
      `--only`-mode trap, the anchor-indent rule, and the formatter-mangling trap).** **Known narrow overlap
      (na-eligibility-audit 2026-08-03, conflict-check § 3): `cross_cutting_satellite_ao_dispatch_batch3_2026_08_01.md`
      carries its own P3 todo to hand-fix ONE of these 82 files
      (`issues/sports_stats_delayed_live_capture_still_dead_post_fix_2026_07_29.md`, still flagged as of this run's live
      check). Not treated as a blocking conflict — both fixes converge on the identical whitespace-only repair, so
      whichever lands first makes the other a no-op; skip re-touching that file if batch3's todo has already landed by
      the time this todo executes.** (repo: unified-trading-pm)
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

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.

- **na-eligibility-audit 2026-08-03 (cross-cutting tranche)**: RECLASSIFY, conflict-check CLEAR — this doc's own
  Progress Log explicitly invited reclassification, and the sole open todo is bounded/mechanical (run an existing
  script, collapse whitespace per its output, verify content-only via `git diff -w`) with a stated done-when. Cleared
  against the shared conflict-check protocol: the only overlap found is a narrow, single-file one with
  `cross_cutting_satellite_ao_dispatch_batch3_2026_08_01.md`'s hand-fix todo (noted inline above, not blocking — an
  idempotent mechanical fix). No finalize-plan companion needed (`doc_type: issue`, structurally exempt per
  `check_finalize_plan_coverage.py`). Flipped `assigned_vm: NA -> planning`, `execution_scope` to `orchestrator-agent`.

- **plan_reconciler 2026-08-10 (cross-cutting tranche, dispatch `agt-33a6ec`)**: refining the trigger condition while
  hand-fixing several NEW instances this run (unrelated to this doc's own todos — found while adding my own notes to
  other plan docs). Confirmed concretely: the corruption is NOT random — it specifically triggers on a multi-paragraph
  note **nested as a continuation of a checkbox list item** (2+ levels of list/checkbox indent), and gets WORSE on each
  successive `prettier --write` pass on the same content (non-idempotent, monotonically increasing indent — matches
  `check_prosewrap_padding.sh --only`'s own doc comment about this). Repro'd live: writing the identical prose as a
  **top-level blockquote** (`> **...**` immediately before the checkbox, not nested under it) survives repeated
  `prettier --write` passes with zero padding growth — 0 violations both before and after. Practical takeaway for any
  agent hand-authoring a multi-paragraph annotation near a checkbox: use a top-level blockquote banner (matching the
  style already used elsewhere in this corpus for dated correction banners), not a nested checkbox-continuation
  paragraph, or expect to re-fight this bug on every commit attempt.
