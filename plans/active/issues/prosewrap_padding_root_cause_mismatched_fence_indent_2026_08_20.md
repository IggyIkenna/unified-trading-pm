---
doc_type: issue
title:
  check_prosewrap_padding's shallow line-level fix (fix_prosewrap_padding.py) doesn't hold when the root cause is a
  mismatched opening/closing code-fence indent — the padding regrows +4sp on every subsequent prettier pass and two
  independent workers shipped fixes that immediately regressed
summary: >-
  /codex/15-runbooks/custody-onboarding-checklist.md tripped check_prosewrap_padding.sh (RED on live-defi-rollout,
  ldr_qg_failure wall) twice in the same hour from two independent CICD escalation workers (agt-bb4764 this doc's
  author, agt-910a14 a peer slot). Both first attempts used the standard repair path (fix_prosewrap_padding.py /
  hand-collapsing the flagged prose lines to the anchor indent) and both verified 0 violations locally — then both
  regressed again within minutes, because the ACTUAL root cause was never touched: 7 fenced code blocks in this doc
  have their closing ``` fence indented to match the deeply-indented CODE content instead of the list-item
  continuation indent (6sp) the opening fence uses. That opening/closing fence indent mismatch confuses prettier's
  markdown reprinter (even under `proseWrap: preserve`, i.e. AFTER f73e218287 already closed the earlier
  proseWrap:always reflow bug at what was believed to be its root) — every single `prettier --write` pass on the file
  re-pads the trailing prose paragraph by +4sp and never converges. Reproduced locally 3x in a row: 14->18->22->26.
  Since check_prosewrap_padding.sh's own fence-line detector deliberately SKIPS fenced code content (by design, to
  avoid flagging legitimate code formatting), it only ever surfaces the SYMPTOM (the trailing prose over-indent), never
  this structural cause — so a worker fixing only the flagged lines is fixing a downstream effect that regrows the
  moment the next prettier pass runs (pre-commit hook, or quickmerge Stage 5's own re-format pass — see the "M1"
  warning quickmerge.sh already emits for this exact reformat-after-sentinel class).
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [prettier, prosewrap, plan-hygiene, tooling, ci, quality-gates]
related:
  [
    prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31,
    prosewrap_padding_corpus_wide_1290_space_2026_08_03,
  ]
created: 2026-08-20
author: worker (slot 7, agt-bb4764, cicd escalation)
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.15
drift_direction: none
parent_epic: infrastructure_master
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Discovered 2026-08-20 while resolving an ldr_qg_failure escalation (agt-bb4764) for
  unified-trading-pm@f49bfafa; confirmed as a distinct, still-open root cause after observing a peer worker's
  fix (unified-trading-pm@ec98ae0d8a, agt-910a14) regress within the same CI cycle. Fixed for this one file at
  unified-trading-pm@8d3f71ff50 by dedenting each closing fence + trailing prose to the 6sp continuation indent;
  verified content-preserving (`git diff -w` empty) and held across a real pre-commit prettier pass.
---

# check_prosewrap_padding root cause #2: mismatched code-fence indent (distinct from the proseWrap:always bug)

## What was found

`/codex/15-runbooks/custody-onboarding-checklist.md` has 7 fenced code blocks (B.2.1/B.2.2/B.2.3/B.2.5/B.2.6/B.3.2/B.3.4)
where the closing ` ``` ` fence is indented to match the deeply-indented code CONTENT (26+ spaces) instead of the
opening fence's list-item-continuation indent (6 spaces, matching every other correctly-behaving continuation line in
this same doc, e.g. B.2.4's `filter: ...` line). This mismatch is invisible to `check_prosewrap_padding.sh`'s own
detector (which explicitly, correctly, skips fence-internal lines) — it only ever sees the downstream symptom, the
trailing prose paragraph immediately after the fence getting progressively over-indented.

Reproduced locally: running `bash scripts/hooks/prettier-autostage.sh <file>` (the exact hook the pre-commit chain and
quickmerge Stage 5 both invoke) repeatedly on the file, WITHOUT touching the fence mismatch, grows the flagged lines'
indent by +4 on every single pass — never converges:

```
pass 0 (baseline, post-shallow-fix): indent 14
pass 1: indent 18
pass 2: indent 22
pass 3: indent 26
```

This happens even with `proseWrap: preserve` already in effect (`.prettierrc` since f73e218287, 2026-08-16) — that
fix closed the reflow-driven padding bug for well-formed docs, but does NOT protect a doc whose fence indentation is
itself malformed. `git diff -w` is empty across all these passes (content-preserving; only leading whitespace moves).

## Why the shallow fix doesn't hold

`fix_prosewrap_padding.py` and hand-collapsing the flagged prose lines both operate ONLY on the lines the checker
names — never on the fence lines that caused the drift. The very next prettier pass (which nothing in the standard
ship path skips — pre-commit hook, quickmerge Stage 5's post-sentinel reformat) re-corrupts the same lines. Two
independent worker sessions hit this in the same CI cycle for the same file (`unified-trading-pm@dbe4915076` this
doc's author, then `unified-trading-pm@ec98ae0d8a` a peer) — both verified clean locally, both regressed within
minutes of landing.

## The real fix

Dedent the closing fence (and its trailing prose paragraph) to match the OPENING fence's indent — the list-item
continuation indent, 6sp in this doc's convention. Applied for this file at `unified-trading-pm@8d3f71ff50`; verified
idempotent-enough to survive a real pre-commit prettier pass (0 violations post-commit) and content-preserving
(`git diff -w` empty).

## Open follow-up

- [ ] [SCRIPT] P2. Audit the rest of the corpus for the same opening/closing-fence indent mismatch pattern —
      `check_prosewrap_padding.sh` only flags a doc AFTER the trailing prose crosses its indent threshold, so a doc
      with a mismatched fence but short/absent trailing prose could be silently carrying the same landmine, waiting
      to trip on some future unrelated prettier pass. A grep-based structural check (compare each fenced block's
      opening-fence indent to its closing-fence indent, corpus-wide) would catch this class directly instead of
      waiting for the symptom.
- [ ] [SCRIPT] P3. Consider extending `check_prosewrap_padding.sh` (or a small companion check) to detect
      opening/closing fence indent mismatches directly — this would let a worker fix the ROOT CAUSE the first time
      instead of a downstream symptom that silently regrows.
