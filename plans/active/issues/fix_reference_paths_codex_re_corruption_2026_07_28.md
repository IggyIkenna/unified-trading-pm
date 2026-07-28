---
doc_type: issue
title:
  fix_reference_paths.py CODEX_RE regex corrupted mid-word "codex/" occurrences — 118 pre-existing hits across 47 files
summary:
  "fix_reference_paths.py's CODEX_RE lookbehind was missing `.`/`-` from its exclusion set, so a bare
  `codex/NN-.../x.md` substring occurring mid-word (e.g. the archived repo name `unified-trading-codex/09-strategy/...`
  in historical prose) got matched and corrupted into `unified-trading-/codex/09-strategy/...`. The regex bug is now
  fixed (unified-trading-pm@<sha>), but the damage it already did to the corpus in a prior run was NOT auto-repaired
  (fixing the regex only prevents future corruption) — 118 occurrences across 47 files, 42 already in plans/archive/
  (low traffic) and 5 in plans/prompts/ (historical phase-based agent prompts, likely superseded by the current
  agent-orchestrator dispatch system — verify before fixing)."
status: active
nature: bug
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, reference-paths, regex-bug, corpus-corruption, tooling]
related: []
created: 2026-07-28
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.1
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
---

# fix_reference_paths.py CODEX_RE corruption — pre-existing damage from the regex bug

## What happened

`scripts/plan-hygiene/fix_reference_paths.py`'s `CODEX_RE` regex (normalizes bare `codex/...` refs to `/codex/...`) used
a negative lookbehind `(?<![\w/])` that excluded word-chars and `/` but **not** `.` or `-`. `check_reference_paths.py`'s
own `BARE_CODEX_RE` (the checker, not the fixer) correctly excludes all four (`(?<![\w/.-])`) — the two regexes drifted
out of sync at some point, and the fixer's looser version is the one that actually writes files.

Consequence: any text where a `codex/NN-.../x.md`-shaped substring occurs **mid-word** — e.g. the archived repo name
`unified-trading-codex/09-strategy/cross-cutting/operational-modes-matrix.md` (prose in an old audit doc describing a
stale README reference in the now-ARCHIVED `unified-trading-codex` repo, per CLAUDE.md "`unified-trading-codex` ARCHIVED
(SSOT = PM's `codex/`)") — got matched at the `codex/09-strategy/...` boundary and rewritten to
`unified-trading-/codex/09-strategy/...`, inserting a spurious `/` and orphaning the `unified-trading-` prefix.

**Caught mid-session (2026-07-28) before being committed once** — the same run also touched
`plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md` this way; that instance was caught and reverted before
shipping. But the corpus-wide `grep -rl` sweep below shows the pattern **already exists 118 times across 47 files**,
meaning an earlier run of the buggy fixer (predating this session) already corrupted real content that WAS committed.

## The regex bug itself: FIXED

`CODEX_RE`/`CODEX_RELATIVE_RE` lookbehinds now match the checker's `(?<![\w/.-])` (unified-trading-pm commit shipped
2026-07-28, same session as this issue doc). This stops **future** runs from corrupting more content. It does **not**
retroactively repair the 118 existing hits — that is this issue's scope.

## Scope of existing damage

```
grep -rln 'unified-trading-/codex\|unified-trading-/plans' --include="*.md" . | grep -v .venv
```

- **118 occurrences across 47 files** (as of 2026-07-28).
- **42 files already under `plans/archive/`** — historical, low-traffic, low-priority to fix (nobody navigates via a
  stale archived doc's prose).
- **5 files under `plans/prompts/`** (`AGENT_PROMPT_PHASE1.md`, `AGENT_PROMPT_PHASE2.md`, `AGENT_PROMPT_PHASE3.md`,
  `AGENT_PROMPT_SPORTS_PHASE2.md`, `add-prettier-to-pre-commit-hooks.md`) — these read like historical phase-based
  agent-dispatch prompts (paste-into-a-new-session scripts) that plausibly predate and are superseded by the current
  `agent-orchestrator` dispatch system described in the workspace `CLAUDE.md`. **Verify whether these are still
  referenced/used anywhere before spending fix effort** — if genuinely dead/superseded, archiving them (not fixing them)
  may be the right move instead.

## Todos

- [ ] [DOC] P3. **Determine liveness of the 5 `plans/prompts/*.md` hits** (`AGENT_PROMPT_PHASE1.md`,
      `AGENT_PROMPT_PHASE2.md`, `AGENT_PROMPT_PHASE3.md`, `AGENT_PROMPT_SPORTS_PHASE2.md`,
      `add-prettier-to-pre-commit-hooks.md`) — grep the corpus + `DOC_INDEX.generated.md` for referrers/usage; these
      read like historical phase-based agent-dispatch prompts predating the current `agent-orchestrator` system. If
      dead, archive them (git mv to `plans/archive/`) instead of fixing the corruption in place; if still live, fix.
- [ ] [DOC] P3. **Fix the corruption in whichever `plans/prompts/*.md` files are confirmed live** — restore
      `unified-trading-/codex/` → `unified-trading-codex/` and `unified-trading-/plans/` → `unified-trading-pm/plans/`
      (verify per-file via `git log -p --follow -- <file>` before a blind replace, in case the surrounding text changed
      since the corruption landed).
- [ ] [DOC] P3. **Fix or explicitly defer the 42 `plans/archive/**` hits** — re-run
      `grep -rln 'unified-trading-/codex\|unified-trading-/plans' --include="*.md" . | grep -v .venv | grep plans/archive/`
      (count may have shifted). Low-traffic historical prose — fixing is optional cleanup, not correctness-critical; if
      deferring, say so explicitly with a reason rather than silently dropping the todo.
- [ ] [REVIEW] P3. **Confirm no other regex in the plan-hygiene toolkit has the same lookbehind-exclusion-set drift**
      (checker vs fixer using different negative-lookbehind character classes) — `check_reference_paths.py`'s
      `BARE_CODEX_RE`/`GOOD_REF_RE`/`BARE_MD_RE` are the reference; grep `scripts/plan-hygiene/*.py` for any other
      `re.compile` pair that SHOULD stay in sync but doesn't.

Do NOT re-run `fix_reference_paths.py` expecting it to auto-repair the existing damage — the regex fix only prevents
_new_ corruption; the already-corrupted strings no longer match any bare-`codex/` pattern (the stray `/` breaks the
`codex/` prefix match), so the fixer is a no-op on them by design now. The repair above is a manual/scripted
find-and-restore, not a re-run of the same tool.

## Done when

- Every `plans/prompts/*.md` hit is either fixed or the doc is confirmed dead and archived instead (with a stated
  reason).
- The `plans/archive/**` hits are fixed OR explicitly deferred with a note that archived-doc prose corruption is
  accepted low-priority debt (operator call, not a worker default).
