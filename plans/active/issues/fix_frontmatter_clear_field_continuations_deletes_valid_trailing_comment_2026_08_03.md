---
doc_type: issue
title:
  fix_frontmatter.py's execution_scope/last_updated continuation-stripper deletes the field's actual VALUE (not just the
  garbage) when a legitimate value is followed by a multi-line trailing comment, silently reverting deliberate operator
  rulings
summary: >-
  Found live while shipping an unrelated fix (2026-08-03): `scripts/plan-hygiene/fix_frontmatter.py`'s
  `_clear_field_continuations()` (run by `quickmerge.sh`'s pre-gate hygiene step) unconditionally strips every indented
  continuation line under `execution_scope:`/`last_updated:` UNLESS the first continuation line starts with a quote
  character — its only guard against deleting a deliberate multi-line value. It does not recognize a THIRD, also
  legitimate pattern: a real single-line value followed by a `#`-prefixed explanatory comment that itself wraps across
  multiple indented lines, e.g.
  `plans/active/issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md` carried
  `execution_scope:\n  local-only # corrected 2026-08-02 (operator ruling on ...): was orchestrator-agent, contradicting
  assigned_vm: NA. Stays NA until ...`. The value line itself (`local-only # ...`) does not start with a quote, so the
  whole continuation block — INCLUDING the real value `local-only` — gets deleted, leaving the field empty; a later
  default-derivation step then re-populated it with the stale value the trailing comment explicitly said was WRONG
  (`orchestrator-agent`), silently re-introducing the exact `execution_scope`/`assigned_vm: NA` contradiction the cited
  2026-08-02 operator ruling had just corrected. Caught only because this session happened to `git diff` before
  committing an unrelated auto-fixer side-effect rather than blindly staging it — a normal `--files`-scoped agent run
  that doesn't diff an incidentally-touched file would have shipped the revert silently.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, frontmatter, fix_frontmatter, quickmerge, data-integrity, regression]
related:
  [
    /plans/active/issues/prek_patch_cache_replays_stale_diff_onto_unrelated_files_2026_07_29.md,
    /plans/active/issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md,
  ]
created: 2026-08-03
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
drift_direction: correct-codex
depends_on: []
source:
  [
    "Discovered incidentally while quickmerge-shipping an unrelated PM doc batch this session (2026-08-03): the pre-gate
    'plan frontmatter auto-fixer' step touched
    plans/active/issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md (a file this session
    never intentionally edited); diffing it before staging showed a deliberate 2026-08-02 operator-ruling comment plus
    its corrected value had been deleted and replaced with the pre-ruling stale value. Reverted the unintended change
    (never shipped) and filed this instead of silently committing it.",
  ]
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    scripts/plan-hygiene/fix_frontmatter.py,
    /plans/active/issues/prek_patch_cache_replays_stale_diff_onto_unrelated_files_2026_07_29.md,
  ]
---

# fix_frontmatter.py deletes a valid value when it's followed by a multi-line trailing comment

## The bug

`_clear_field_continuations()` (`scripts/plan-hygiene/fix_frontmatter.py:311-352`) exists to strip ACCIDENTAL YAML-fold
garbage trailing `execution_scope:`/`last_updated:` (a real, previously-fixed bug class — see the related
`prek_patch_cache_replays_stale_diff_onto_unrelated_files_2026_07_29.md` citation in its own docstring). Its only guard
against deleting a genuine deliberate value: check whether the FIRST continuation line, stripped, starts with a quote
character (`'` or `"`) — if so, assume it's an intentional quoted multiline scalar and leave it alone; otherwise strip
the entire continuation block unconditionally.

This misses a third, also-legitimate pattern already live in the corpus: a real single-line value immediately followed
by a `#`-prefixed comment, itself wrapped across several further indented comment-only lines, e.g.:

```yaml
execution_scope:
  local-only # corrected 2026-08-02 (operator ruling on
  # plan_reconcile_parked_operator_decisions_2026_08_02.md na-eligibility-audit item 20, option A): was
  # orchestrator-agent, contradicting assigned_vm: NA. Stays NA until the shared-host RAM exhaustion mechanism
  # (condition mdps-e2e-shared-host-teardown-fixed) is also closed, not just the partial root-cause on todo 1.
```

`local-only` does not start with a quote, so the function's `else` branch (line 346-348) deletes the WHOLE continuation
block, value included — not just the trailing comment. `execution_scope` is left with no value on its own line; a later
default-derivation step in the same fixer then repopulates it, landing on `orchestrator-agent` (the pre-ruling value the
deleted comment explicitly flagged as wrong) rather than `local-only`. Net effect: a deliberate, reasoned, dated
operator correction is silently reverted to the exact contradiction (`execution_scope: orchestrator-agent` alongside
`assigned_vm: NA`) it had fixed — and every future fixer/quickmerge run re-reverts it again, since the comment carrying
the explanation is now gone and nothing marks the field as "don't touch."

## Why this matters

This hygiene step runs as part of `quickmerge.sh`'s pre-gate on every `--agent --files`-scoped ship that happens to
touch ANY plan under `plans/active/` (not just files the agent intentionally edited — it scans the whole corpus, per the
earlier `prek_patch_cache_replays_stale_diff_onto_unrelated_files_2026_07_29.md` precedent this exact function was built
to fix one instance of). An agent that stages `--files` without diffing every incidentally-touched file first ships this
silently — exactly the failure mode `commit-push-flip-rule`'s pre-commit `git status && git diff --cached --stat` step
exists to catch, except this corruption happens to a file the agent never staged in the first place, so a diff scoped to
intentionally-changed files won't surface it either.

## Todos

- [x] ✅ [BACKEND] P1. Fix `_clear_field_continuations()` to recognize "value + trailing `#`-comment, possibly wrapped
      across further indented comment-only lines" as a fourth legitimate pattern, distinct from both accidental-fold
      garbage and a quoted multiline scalar — e.g. treat any continuation line whose STRIPPED content starts with `#` as
      a comment continuation (keep it, or strip only the comment while preserving the value line itself), and only apply
      the existing garbage-strip to continuation lines that carry neither a leading quote nor a leading `#`. Add a
      regression test using the exact `worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md` shape as
      a fixture. Repo: unified-trading-pm. — unified-trading-pm@458ba0180
- [ ] [DATA] P2. Audit `plans/active/**/*.md` for any OTHER `execution_scope`/`last_updated` field carrying this same
      "value + multi-line trailing comment" shape that may have already been silently corrupted by a prior fixer run
      before this bug was caught — grep for `execution_scope:$` (bare, no inline value) followed by an indented
      non-quote-non-comment line, and cross-check each hit's git blame for a fixer commit that removed an adjacent
      operator-ruling comment. Repo: unified-trading-pm.

## Progress Log

- **2026-08-03**: filed after catching (and reverting, not shipping) one live incident — see `source` above.
- **2026-08-03 (cicd plan_health escalation, agt-ab3285)**: RECLASSIFY `assigned_vm: NA` → `planning`
  (`execution_scope: local-only` → `orchestrator-agent`). Both todos are precisely-scoped, deterministic-outcome work
  (fix a named function's continuation-line classification logic + add a named regression-test fixture; audit the corpus
  for the same shape via a stated grep+git-blame recipe) — a bounded bug fix, not an open-ended judgment call defaulted
  to NA. Conflict-check: no other active plan/issue references `_clear_field_continuations` or this bug shape — cleared.
  Done as part of resolving the `check_na_corpus_ratchet` hard-gate failure (361 > baseline 360) by fixing a genuine
  misclassification rather than raising the ratchet.
- **2026-08-03 (slot 6, backend_engineer)**: shipped todo 1 — `_clear_field_continuations()` now treats a first
  continuation line with real content before an unquoted `#` as a value+trailing-comment pattern and preserves the whole
  block, instead of only guarding on a leading quote. Added
  `tests/unit/test_fix_frontmatter_clear_field_continuations.py` using the exact
  `worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md` shape as a regression fixture, plus coverage
  confirming the quoted-scalar guard and the accidental-fold-garbage strip both still work unchanged.
  `unified-trading-pm@458ba0180`, full quality-gates.sh green (1663 passed/11 skipped, coverage 69.99%). Todo 2 ([DATA]
  P2 corpus audit) remains open for a data_engineering worker.
