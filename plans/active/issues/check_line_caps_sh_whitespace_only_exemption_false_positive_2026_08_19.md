---
doc_type: issue
title: check_line_caps.sh SCOPED-mode whitespace-only-repair exemption uses `--cached` diff — false-positive on an
  edited-but-unstaged file
summary: >-
  `scripts/plan-hygiene/check_line_caps.sh`'s SCOPED-mode "whitespace-only-repair" exemption
  (operator ruling 2026-08-15) checks `git diff --cached -w -- "$f"` — the STAGED diff. When the script is invoked
  directly on a file with real, unstaged (working-tree-only) edits — exactly the shape
  `sports_consolidated_native_ao_extract_2026_07_25_finalize.md` todo 1 itself instructs a worker to run
  ("check_line_caps.sh <path>" before staging, to decide whether an edit is safe to make) — `--cached` sees zero
  staged content and the diff is trivially empty, so the exemption fires and the script reports "allowed" even
  though the actual (unstaged) change is substantive, non-whitespace content. Confirmed live 2026-08-19: editing
  `sports_consolidated_closeout_2026_07_19.md` from 1000L to 1002L with real prose changes (5 checkbox flips +
  citations, 29 insertions/27 deletions per `git diff --stat`) made the script print `SOFT ... 1002L ... (over cap
  pre-existing; allowed — whitespace-only repair, git diff -w empty, operator ruling 2026-08-15)` and exit 0 — while
  a direct `git diff -w -- <file>` (working-tree, not staged) showed 75 lines of genuine non-whitespace diff. Did NOT
  rely on the false exemption; trimmed the edit back under the 1000L cap instead.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, line-caps, check_line_caps, quality-gate, false-positive]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25_finalize.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/issues/check_line_caps_issues_subdir_full_corpus_glob_gap_2026_08_19.md,
  ]
created: "2026-08-19"
parent_epic: plan_hygiene_master
author: plan_reconciler
source: >-
  Found live while executing `sports_consolidated_native_ao_extract_2026_07_25_finalize.md` todo 1's own explicit
  instruction to run `check_line_caps.sh` against the parent doc before editing it.
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
resolved_by:
archive_exempt:
locked_by:
locked_since:
drift_direction: advance-code
depends_on: []
context_scope:
  [scripts/plan-hygiene/check_line_caps.sh, /plans/active/sports_consolidated_closeout_2026_07_19.md]
---

# check_line_caps.sh's whitespace-only-repair exemption checks the wrong diff (`--cached` vs. working tree)

## What I found

`scripts/plan-hygiene/check_line_caps.sh:196` (SCOPED-mode whitespace-only-repair exception, operator ruling
2026-08-15, `BLK-d942f2f7`):

```bash
if [ -z "$(git -C "$PM_DIR" diff --cached -w -- "$f" 2>/dev/null)" ]; then
  WHITESPACE_ONLY_REPAIR="1"
fi
```

This checks the **staged** diff (`--cached`). The exception is documented as covering "a staged diff to an
already-over-cap doc that is byte-identical modulo whitespace" — correct when the caller has already run `git add`
before invoking the check (e.g. the prek pre-commit hook, which always operates on the index). **But the same script
is also the sanctioned way to check an UNSTAGED edit before deciding whether to stage it at all** —
`sports_consolidated_native_ao_extract_2026_07_25_finalize.md` todo 1 literally instructs exactly this:
"**First check whether the parent file is still over the line-cap**
(`bash scripts/plan-hygiene/check_line_caps.sh plans/active/sports_consolidated_closeout_2026_07_19.md`) — if still
HARD-blocked, do NOT force the edit." In that invocation shape, nothing is staged yet, so
`git diff --cached -w -- "$f"` compares the index (== HEAD, since nothing staged) against HEAD — **trivially empty,
regardless of what the actual working-tree edit contains.** The exemption fires on every unstaged over-cap edit, not
just genuinely whitespace-only ones.

**Confirmed live** (2026-08-19, `plan_reconciler` sports-tranche run): edited
`sports_consolidated_closeout_2026_07_19.md` (real content: 5 checkbox flips `[ ]`→`[x]` + citation prose, replacing
verbose "Done when:" trailers), growing it from exactly 1000L to 1002L, WITHOUT staging. Ran
`check_line_caps.sh plans/active/sports_consolidated_closeout_2026_07_19.md`:

```
  SOFT    sports_consolidated_closeout_2026_07_19.md  1002L  todos=69  (over cap pre-existing; allowed —
  whitespace-only repair, `git diff -w` empty, operator ruling 2026-08-15)
✅ check_line_caps: staged plan(s)/epic(s) within cap
```

Independently verified this claim against the actual (working-tree) diff:

```
$ git diff -w -- plans/active/sports_consolidated_closeout_2026_07_19.md | wc -l
75
$ git diff --stat -- plans/active/sports_consolidated_closeout_2026_07_19.md
 .../sports_consolidated_closeout_2026_07_19.md | 56 +++++++++++-----------
 1 file changed, 29 insertions(+), 27 deletions(-)
```

75 lines of non-whitespace diff, 29/27 insertions/deletions — definitively not whitespace-only. The script's own
exemption message was false for this diff.

## Why it matters

The 2026-07-24 ruling is explicit: line caps are "a REAL hard gate ... no exceptions." The whitespace-only exemption
exists to let a genuinely content-neutral repair (e.g. `fix_prosewrap_padding.py`'s de-indent) through an
already-over-cap doc without being blocked by a pre-existing violation it didn't cause. That's a sound carve-out **for
the staged-diff case it was built and tested for**. But as shown above, the SAME check silently mis-fires for the
equally-common unstaged-check pattern — which is not a hypothetical: it's the literal, cited invocation in a live,
`assigned_vm: planning` finalize plan's own todo 1. Any worker following that todo's instructions verbatim, on a
doc sitting exactly at cap, could push it over cap while genuinely believing (per the tool's own "allowed" verdict)
that the edit is safe. This run did not fall for it (independently verified before trusting it, then trimmed the
edit back under cap instead) — but the tool's job is to make that independent verification unnecessary, and right
now it can't be trusted for this invocation shape.

**Scope note**: this is a different bug from the sibling `plans/active/issues/*.md`-glob-gap issue filed the same day
by a separate `/plan-reconcile sports_master` run (`check_line_caps_issues_subdir_full_corpus_glob_gap_2026_08_19.md`)
— that one is about full-corpus mode never scanning the `issues/` subdirectory at all; this one is about SCOPED mode's
whitespace-exemption comparing against the wrong git ref. Both live in the same script, filed separately per that
sibling issue's own precedent (root-causing either correctly requires careful re-verification of the OTHER
exemptions in the same SCOPED-mode block, not a same-file mechanical fix this pass should improvise).

## Recommended decision

**A: Fall back to a working-tree diff when nothing is staged. [WORKER REC]** — e.g.
`git -C "$PM_DIR" diff --cached -w -- "$f"`, and if that's empty AND `git -C "$PM_DIR" diff --cached --name-only -- "$f"`
shows the file isn't actually staged, additionally check `git -C "$PM_DIR" diff -w -- "$f"` (working tree vs HEAD)
before concluding whitespace-only. This preserves the exemption's original intent (staged pre-commit check) while
correctly handling the unstaged pre-flight-check invocation shape.
**B: Document the invocation contract instead — SCOPED mode is "staged-only," callers must `git add` before checking.**
Simpler, but requires updating every doc/plan that currently instructs an unstaged pre-flight check (at least
`sports_consolidated_native_ao_extract_2026_07_25_finalize.md` todo 1, likely others workspace-wide) and removes a
genuinely useful "can I even make this edit" pre-check.
**C: Leave as-is, rely on workers independently verifying (as this run did).** Rejected as the recommendation — the
whole point of a mechanical gate is not needing a human/agent to re-derive the check by hand every time.

## Todos

- [ ] [SCRIPT] P2. Fix `check_line_caps.sh`'s SCOPED-mode whitespace-only-repair exception (line ~196) to correctly
      detect an unstaged working-tree diff when nothing is staged, per recommendation A above. Add a regression test
      or scripted repro: create a doc at exactly `PLAN_HARD_CAP` lines, make a real (non-whitespace) unstaged edit
      that pushes it over cap, run `check_line_caps.sh <path>` unstaged, and assert it reports a HARD failure, not
      the whitespace-only-repair pass. Done when: the repro above fails correctly, and the existing legitimate
      staged-whitespace-only case (the original 2026-08-15 motivating scenario) still passes.
- [ ] [DOC] P3. Audit other plans/finalize-plan todos that instruct an unstaged `check_line_caps.sh <path>` pre-flight
      check (grep the corpus for the pattern) and confirm none of them are currently relying on a false "allowed"
      verdict for a doc that's actually genuinely blocked.

## Progress Log

- **2026-08-19 (plan_reconciler, sports tranche, dispatch agt-07473e)**: filed. Found live while following
  `sports_consolidated_native_ao_extract_2026_07_25_finalize.md` todo 1's own instructed pre-flight check. Root-caused
  by direct code read (line 196) plus independent verification against the actual diff (not just distrust — measured
  and confirmed the false-positive). Not fixed inline — root-causing correctly requires care around the sibling
  exemptions in the same SCOPED-mode block; genuinely new scoped work, per this doc's own Scope note.
