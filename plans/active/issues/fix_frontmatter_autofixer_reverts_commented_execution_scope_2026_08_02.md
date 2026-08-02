---
doc_type: issue
title: fix_frontmatter.py auto-fixer reverts a deliberate, comment-documented execution_scope correction
summary: >-
  scripts/plan-hygiene/fix_frontmatter.py (run as part of quality-gates.sh) mis-normalizes a multi-line YAML
  block-scalar execution_scope value with an inline explanatory comment, silently collapsing it back to the stale value
  the comment says was deliberately corrected away from.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, frontmatter, auto-fixer, regression]
related:
  [
    /plans/active/issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md,
    /plans/active/issues/plan_reconcile_parked_operator_decisions_2026_08_02.md,
  ]
created: "2026-08-02"
last_updated: "2026-08-02"
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.1
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Found while running quality-gates.sh for plans_archive_reference_path_hygiene_2026_08_02.md (slot-8, 2026-08-02).
assigned_role: review
drift_direction: correct-codex
---

# fix_frontmatter.py auto-fixer reverts a deliberate execution_scope correction

## What I found

Running `bash scripts/quality-gates.sh` in `unified-trading-pm` auto-fixes
`plans/active/issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md`'s frontmatter every time,
reporting `FIXED ...: stripped stray execution_scope continuation lines, set execution_scope=orchestrator-agent`. The
file's committed value is a multi-line YAML block scalar with an inline comment recording a deliberate 2026-08-02
operator-ruling correction:

```yaml
execution_scope:
  local-only # corrected 2026-08-02 (operator ruling on
  # plan_reconcile_parked_operator_decisions_2026_08_02.md na-eligibility-audit item 20, option A): was
  # orchestrator-agent, contradicting assigned_vm: NA. Stays NA until the shared-host RAM exhaustion mechanism
  # (condition mdps-e2e-shared-host-teardown-fixed) is also closed, not just the partial root-cause on todo 1.
```

The fixer's frontmatter normalizer treats this as malformed (a stray multi-line continuation) and rewrites it to a
single-line `execution_scope: orchestrator-agent` — silently reverting the ruling the comment documents, not just
reformatting it. Any worker who runs a full `quality-gates.sh` in this repo and stages/commits broadly (or doesn't
`git restore` unrelated auto-fixed files) will re-ship the stale value.

## Why it matters

This is a general auto-fixer defect (any frontmatter field authored as a commented multi-line YAML block scalar is at
risk, not just this one file), and it silently undoes a real operator ruling rather than erroring loudly. Low
blast-radius per-incident (caught this time by not staging unrelated files), but it will keep recurring on every QG run
until the file's frontmatter is reshaped or the fixer is taught to preserve/ignore commented block scalars.

## Recommended decision

Either (a) reshape `execution_scope` in the affected file to a single-line value with the explanation moved to prose in
the doc body (removes the trap for this one file), or (b) teach `scripts/plan-hygiene/fix_frontmatter.py` to leave a
field's value untouched when it's already a valid (if multi-line/commented) YAML scalar equal in effect to what it would
normalize to, only touching genuinely malformed values. (b) is more durable since other docs may hit the same shape.

## Todos

- [ ] [SCRIPT] P3. Fix `scripts/plan-hygiene/fix_frontmatter.py` so it does not silently overwrite a
      multi-line/commented `execution_scope` (or any other field) block scalar that already parses to a valid value —
      either skip normalization when the parsed value is already valid, or refuse + report instead of silently
      rewriting. (repo: unified-trading-pm)
- [ ] [DOCS] P3. Reshape `worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md`'s `execution_scope`
      field to a single-line value (move the ruling explanation into the doc body/Progress Log) so it stops being
      re-mangled on every QG run until todo 1 lands. (repo: unified-trading-pm)

## Progress Log

- **2026-08-02** — Filed by slot-8 while shipping `plans_archive_reference_path_hygiene_2026_08_02.md`; did not stage
  the auto-fixer's change (`git restore`d it) so the ruling's correction survives on `live-defi-rollout`.
