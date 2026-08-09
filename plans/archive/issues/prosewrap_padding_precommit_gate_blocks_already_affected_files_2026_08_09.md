---
doc_type: issue
title:
  check_prosewrap_padding.sh --only precommit gate (added 2026-08-09) blocks ANY commit to a plan/issue doc already
  carrying legacy prosewrap corruption — prettier's own reformat is non-idempotent and the gate compares post-reformat
  content against HEAD
summary: >-
  `check_prosewrap_padding.sh --only` was wired into the plan-hygiene precommit hook today (2026-08-09) to catch NEW
  prosewrap-padding instances per commit. It runs AFTER `prettier-autostage` in the same hook chain and compares the
  file's POST-prettier content against `git show HEAD:<path>` (also post-some-earlier-prettier-pass). Reproduced live
  and in isolation: prettier's proseWrap reflow for a multi-line paragraph nested as a 2nd+ paragraph in a checkbox list
  item is NOT idempotent — a fresh 2-paragraph fixture's continuation line lands at 10 spaces on pass 1, then 14 on pass
  2, growing further on every subsequent pass. Any commit that touches a file already containing such content (the
  overwhelming majority of active plans — every "DONE" evidence block in this corpus uses this exact
  multi-paragraph-per-todo shape) triggers prettier-autostage's mandatory reformat, which shifts indentation upward
  (observed +4 to +8 per pass on real corpus files), producing a signature not present at HEAD — which
  check_prosewrap_padding --only then correctly, but disruptively, flags as a hard commit block. This is NOT caused by
  the committing worker's own edit content — reproduced with prettier run on git HEAD content with ZERO edits (isolated
  copy, no git operations): padding grew anyway.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [prettier, prek, plan-hygiene, prosewrap, ci-regression, tooling]
related:
  [
    /plans/archive/issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md,
    /plans/active/issues/prosewrap_padding_corpus_wide_1290_space_2026_08_03.md,
    /scripts/plan-hygiene/check_prosewrap_padding.sh,
    /scripts/hooks/prettier-autostage.sh,
    /plans/active/prediction_satellite_ao_dispatch_batch6_2026_07_29.md,
  ]
created: 2026-08-09
author: slot-19 (data_engineering)
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
drift_direction: advance-code
depends_on: []
source:
  [
    "Discovered 2026-08-09 (slot 19, data_engineering) while flipping a checkbox + appending evidence on
    prediction_satellite_ao_dispatch_batch6_2026_07_29.md (todo 5, Kalshi credential/paper-order-verify) — the commit
    was blocked by check_prosewrap_padding (--only), even though the flip + appended evidence used the SAME
    multi-paragraph-per-todo convention already used throughout that same file by OTHER, untouched todos.",
  ]
resolved_by:
  "todo DONE 2026-08-09 (slot 14): unified-trading-pm@89517ae041 + 707623d403, verified against this doc's own repro
  cases."
locked_by:
locked_since:
supersedes:
superseded_by:
---

> **🟢 ARCHIVED 2026-08-09** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Resolution evidence carried in `resolved_by:`. No content was rewritten.

# check_prosewrap_padding --only precommit gate blocks any commit to an already-affected file

## What I found

Wiring `check_prosewrap_padding.sh --only` into the plan-hygiene precommit hook today (2026-08-09, per the script's own
header comment: "2026-08-09, precommit migration") closes a real gap (no precommit-time enforcement existed before), but
has an unintended interaction with the ALSO-mandatory `prettier-autostage` hook that runs earlier in the SAME hook
chain, on the SAME file:

1. **Reproduced live**: flipping one checkbox + appending one evidence paragraph to
   `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` (todo 5) triggered `prettier-autostage` to reformat the WHOLE
   file (prettier is not diff-scoped — it re-serializes the entire document). This shifted indentation on ~182 lines
   throughout the file, including paragraphs I never touched (e.g. the pre-existing "RULED 2026-08-06" paragraph on the
   SAME todo, whose CONTENT I did not edit, shifted from 6 to 14 leading spaces). `check_prosewrap_padding --only` then
   flagged all of these as "new" (the check's signature includes the exact indent amount, so any shift — even to
   already-corrupted content — produces a signature absent from HEAD).
2. **Reproduced in isolation, with ZERO edits**: copied `git show HEAD:<path>` to a scratch file (no git operations, no
   content changes) and ran `npx prettier@3.9.5 --write` on it directly. Indentation on the file's already-corrupted
   paragraphs grew further (e.g. 194→198, 174→178, 196→200, 218→222 leading spaces) purely from re-running prettier on
   unchanged content.
3. **Reproduced with a minimal fixture** (8-line `.md`, a single checkbox item with 2 paragraphs, never before touched
   by prettier): pass 1 produces a continuation line at 10 spaces (under the check's 14-space threshold); pass 2 on that
   SAME pass-1 output produces 14 spaces (at the threshold — now flagged). This is the exact non-idempotent-reflow bug
   already root-caused in `prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md` (that doc's own conclusion:
   no bounded config-side fix exists — it shipped a corpus-wide-baseline lint check instead,
   `prosewrap_padding_corpus_wide_1290_space_2026_08_03.md` tracks the still-in-progress hand-repair of ~80
   already-affected files).

**The new failure mode**: because prettier's reflow is non-idempotent and MONOTONIC (each pass adds more padding, never
converges or stabilizes), and because `--only` compares the file's POST-prettier state (this commit) against HEAD's
state (itself the product of some EARLIER prettier pass), any file that has ALREADY been reformatted at least once by
prettier will show a "new" violation on its NEXT touch — regardless of what the committing worker actually changed.
Given the multi-paragraph-per-todo evidence-block convention is used pervasively across this corpus's active plans
(every "DONE"/"RULED"/partial-progress note follows this shape), this precommit gate, as currently wired, is on a path
to block routine plan-flip commits fleet-wide as more files accumulate at least one prior prettier pass.

## Why it matters

- Blocks the mandatory Commit+Push+Flip HARD RULE (CLAUDE.md) for any todo on an already-affected plan/issue doc — a
  worker cannot complete the required same-turn flip through the standard path.
- The check's own intent (stop a commit from making prosewrap corruption WORSE) is sound; the defect is that it
  currently penalizes a worker for prettier's OWN mandatory, unavoidable, unrelated side effect, not for anything the
  worker's actual diff introduced.
- Likely to recur on every subsequent `docs(plans):` commit to any file this gate has already fired on once, since
  flagging → hand-repair (if attempted) → next mandatory prettier pass → flagged again is not a convergent loop
  (confirmed: 2 prettier passes on the same content never converge, they compound).

## Recommended decision (not adjudicated here — architecture/tooling call)

- **(A) Scope `--only`'s comparison to the WORKER'S OWN diff, not the post-prettier file.** Diff the pre-prettier staged
  content (what the worker actually wrote) against HEAD to find genuinely new violation-shaped lines; ignore shifts that
  are provably attributable to prettier's own reformat pass (e.g. by running the detector on both the pre- and
  post-prettier versions of UNCHANGED lines and excluding any line whose underlying TEXT — not indent — is unchanged
  from HEAD). This directly fixes the root interaction bug.
- **(B) Move `check_prosewrap_padding --only` to a warn-only (non-blocking) precommit step** until the corpus-wide
  hand-repair (`prosewrap_padding_corpus_wide_1290_space_2026_08_03.md`) has cleared enough of the existing corpus debt
  that the interaction with prettier's non-idempotency stops firing on ordinary commits. Keep the full-sweep
  (non-`--only`) ratchet as the enforcement mechanism in the meantime (it already exists and is unaffected by this
  specific bug).
- **(C) Fix prettier's non-idempotency directly** (root-cause a stable, convergent proseWrap output for multi-paragraph
  list-item continuations) — the 2026-07-31 investigation already concluded this needs "broad tradeoff" analysis, not a
  bounded fix; revisit only if (A)/(B) prove insufficient.

[WORKER REC]: (A) — it fixes the actual interaction defect without weakening the gate's intent or waiting on the
(already-stalled) corpus-wide hand-repair to finish.

## Todos

- [x] ✅ [SCRIPT] P1. Implement recommendation (A) — DONE 2026-08-09 (slot 14, two-part fix). First pass
      (`unified-trading-pm@89517ae041`) stripped the `over-indent(NN)` exact-depth number before comparing against
      HEAD's own violations — insufficient alone: it missed the common case where HEAD's line sat under
      `INDENT_THRESHOLD` (never flagged there) and only crossed it via THIS commit's prettier pass, still reading as
      "new". Follow-up (`unified-trading-pm@707623d403`) adds `_all_content_previews()` comparing against ALL of HEAD's
      content, not just its violations. **Confirmed against this doc's own repro §1**: the exact blocked commit now
      passes (`✅ 0 new violation(s)`). **Confirmed both negative-case directions in isolation**: pre-existing text
      reflowed past threshold → not flagged; genuinely new over-indented text → still flags (`❌ ... exit 1`).
      Full-sweep (non-`--only`) mode unchanged. (repo: unified-trading-pm)

## Progress Log

- **2026-08-09 (slot 19, data_engineering)**: filed while blocked mid-task on
  `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 5's required plan-flip commit — see that plan's Progress
  Log / todo 5 evidence for the actual code deliverable (already shipped, unaffected by this issue). Reported as
  `/blocked` to main with this doc as the citation.
- **2026-08-09 (slot 14, data_engineering)**: hit the identical wall independently while flipping N1b's checkbox on
  `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` (unrelated task). Implemented + verified
  recommendation (A) rather than working around it — see todo above for evidence.
