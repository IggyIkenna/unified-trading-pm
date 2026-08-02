---
doc_type: plan
title: Scoped reference-path hygiene pass over plans/archive/
summary: >-
  Run scripts/plan-hygiene/fix_reference_paths.py over the plans/archive/ population specifically to clear the
  check_reference_paths format/exist regression (+47/+14 over baseline) that an active-corpus-only pass cannot reach.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, reference-paths, ratchet, mechanical]
related:
  [
    /plans/active/issues/plan_reconcile_parked_operator_decisions_2026_08_02.md,
    /codex/11-project-management/cross-reference-path-convention.md,
  ]
created: 2026-08-02
last_updated: 2026-08-02
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: review
drift_direction: correct-codex
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: "Operator ruling on plan_reconcile_parked_operator_decisions_2026_08_02.md § 4, option A, 2026-08-02."
---

# Scoped reference-path hygiene pass over `plans/archive/`

## Why this plan exists

`run_hygiene_sweep.sh --ci`'s `check_reference_paths` gate measured RED against baseline on 2026-08-02
(`plan_reconcile_parked_operator_decisions_2026_08_02.md` § 4): format violations 208 vs baseline 161 (**+47**), exist
violations 915 vs baseline 901 (**+14**). The violations are concentrated in `plans/archive/` — out of
`/plan-reconcile`'s audit scope (active corpus only) but inside the ratchet's measured population, so no active-corpus
pass can clear it. `scripts/plan-hygiene/fix_reference_paths.py` already globs `plans/**/*.md` (so `plans/archive/` is
already in its default scope, no code change needed) — this plan is the tracked unit for actually running it and
reviewing the diff, per the operator's ruling that a scoped run is "the only thing that will move that number."

## Todos

- [ ] [SCRIPT] P2. Run `python3 scripts/plan-hygiene/fix_reference_paths.py --dry-run` and read the full output. Two
      independent passes: (1) codex refs anywhere in file content normalized to `/codex/...`; (2) bare `.md` filenames
      in `related:` frontmatter resolved against the live corpus and rewritten to `/plans/<found-relative-path>`.
      Confirm which of the reported changes actually land under `plans/archive/**` (the codex-ref pass touches `codex/`
      files too — those are docs-reconcile's scope, not this plan's; scope this plan's apply to the `plans/archive/**`
      subset only).
- [ ] [SCRIPT] P2. Triage the `AMBIGUOUS`/`UNRESOLVED` entries the dry-run reports for any `plans/archive/**` file —
      these are left untouched by design (never guessed); each either needs its `related:` entry hand-disambiguated to
      the correct one of the reported candidates, or is a genuine dangling reference to record separately.
- [ ] [SCRIPT] P2. Run `python3 scripts/plan-hygiene/fix_reference_paths.py` (apply) scoped to the reviewed
      `plans/archive/**` changes from todo 1, stage by name, ship via
      `bash scripts/quickmerge.sh "docs(plans): fix_reference_paths.py pass over plans/archive/" --agent --files '<paths>'`.
- [ ] [VERIFY] P2. Re-run `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` and confirm `check_reference_paths`
      format/exist counts have dropped back toward the 161/901 baseline (allow for any newly-added legitimate refs
      elsewhere in the corpus since 2026-08-02 — the done-when is "the +47/+14 regression is gone", not an exact
      absolute count match).

## Progress Log

- **2026-08-02** — Filed per the operator's ruling on `plan_reconcile_parked_operator_decisions_2026_08_02.md` § 4,
  option A.
