---
doc_type: plan
title: Scoped reference-path hygiene pass over plans/archive/ — finalize
summary: >-
  Gated closeout for plans_archive_reference_path_hygiene_2026_08_02.md — machine-held via depends_on + gate_on_depends
  until both of that plan's todos are done. Re-verifies the reference-path ratchet actually moved (check_reference_paths
  back at/below the pre-regression baseline: format 161, exist 901), confirms no AMBIGUOUS/UNRESOLVED entry was silently
  dropped, and archives this plan pair once confirmed.
status: superseded
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, reference-paths, ratchet, mechanical, finalize]
related:
  [
    /plans/archive/2026_08/plans_archive_reference_path_hygiene_2026_08_02.md,
    /plans/archive/2026_08/plans_archive_reference_path_hygiene_finalize_2026_08_02.md,
    /codex/11-project-management/cross-reference-path-convention.md,
  ]
created: 2026-08-02
last_updated: "2026-08-03"
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.04
assigned_role: review
drift_direction: correct-codex
locked_by:
locked_since:
supersedes:
superseded_by: plans_archive_reference_path_hygiene_finalize_2026_08_02
depends_on: [plans_archive_reference_path_hygiene_2026_08_02]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/plans_archive_reference_path_hygiene_2026_08_02.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched (`assigned_vm: planning`) plan needs a gated
  finalize plan; this one shipped without its pair, tripping `check_finalize_plan_coverage.py`'s ratchet (baseline 0,
  regression 1). Authored same-session to close the regression, mirroring the shape of existing finalize plans (e.g.
  ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md).
---

# Scoped reference-path hygiene pass over `plans/archive/` — finalize

> **🟡 SUPERSEDED 2026-08-03 — duplicate finalize plan, never executed, and its cited baseline numbers (161/901) were
> already stale even before that.** This doc, `plans_archive_reference_path_hygiene_finalize_2026_08_02.md` (same
> creation day), and `plans_archive_reference_path_hygiene_2026_08_02_finalize_2026_08_03.md` (2026-08-03) were three
> independently-authored gated finalize plans for the same parent. All three were still `status: active`/queued with
> zero todos executed when this was found (live backlog check: none dispatched). This doc's own numbers (format 161,
> exist 901) reference the pre-`dfdb0887` baseline, already superseded by a separate fix before this doc could ever run.
> The actual reconciliation + archival ritual ran under `plans_archive_reference_path_hygiene_finalize_2026_08_02.md`
> (see its own banner for the full 3-way disposition). No unique content lost. Archived alongside the parent + its
> executing finalize doc in the same commit.

## Todos

- [ ] [SCRIPT] P2. **Re-verify the ratchet actually moved, not just that the apply ran.** Re-run
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` (or the standalone `check_reference_paths` checker it wraps)
      and confirm format violations are back at/below the pre-regression baseline (161) and exist violations at/ below
      baseline (901) — the two numbers named in the source plan's own "Why this plan exists" section. If either is still
      above baseline, re-open a follow-up todo naming the specific still-violating files rather than closing this doc.
      **NOT EXECUTED — superseded**, see banner above; also these baseline numbers were already stale (see banner).
- [ ] [REVIEW] P2. **Spot-check the AMBIGUOUS/UNRESOLVED triage.** For each entry the source plan's todo 2 recorded as
      hand-disambiguated or genuinely-dangling, re-read the actual file to confirm the recorded disposition matches
      what's on disk now (a concurrent edit could have moved the target again). Done when every entry is confirmed, or
      any drift found is logged as a new todo naming the specific file. **NOT EXECUTED — superseded**, see banner above.
- [ ] [PLAN] P2. **Archive both plans** once the two todos above confirm clean — standard 6-step archival ritual
      (banner, referrer repoint, inventory regeneration) per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`. **NOT EXECUTED — superseded**, see banner
      above; archival actually performed under `plans_archive_reference_path_hygiene_finalize_2026_08_02.md`.
