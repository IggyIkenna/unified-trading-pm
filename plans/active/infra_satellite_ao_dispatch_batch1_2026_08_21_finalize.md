---
doc_type: plan
title: Finalize — infra satellite AO batch 1 (wave 2) close-out
summary: >-
  Gated finalize companion for infra_satellite_ao_dispatch_batch1_2026_08_21.md — independently re-verifies both
  items' completion evidence (the check_line_caps.sh full-corpus glob fix and the ~694-script # Epic: header sweep),
  reconciles the two source docs' own checkboxes, and performs the completion and archival ritual once the batch
  reaches its declared terminal state.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ao-dispatch, finalize, batch-1, plan-hygiene, archival]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch1_2026_08_21.md,
    /plans/active/issues/check_line_caps_issues_subdir_full_corpus_glob_gap_2026_08_19.md,
    /plans/active/epic_taxonomy_restructure_and_html_reconcile_2026_08_18.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.16
assigned_role: infra
effort: low
thinking_tier: mechanical
depends_on: [infra_satellite_ao_dispatch_batch1_2026_08_21]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/infra_satellite_ao_dispatch_batch1_2026_08_21.md,
    /plans/active/issues/check_line_caps_issues_subdir_full_corpus_glob_gap_2026_08_19.md,
    /plans/active/epic_taxonomy_restructure_and_html_reconcile_2026_08_18.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
source: >-
  na-eligibility-audit, infra tranche wave 2, 2026-08-21 — every assigned_vm: planning plan needs a gated finalize
  companion (/plans/active/task_template.md §4); batch1 carries 2 open todos so the single-todo carve-out does not
  apply.
drift_direction: advance-docs
---

# Finalize — infra satellite AO batch 1 (wave 2) close-out

Machine-held (`gate_on_depends: true`) until every todo in `infra_satellite_ao_dispatch_batch1_2026_08_21.md` is
done. Do not start manually before then.

## Todos

- [ ] [REVIEW] P2. Independently re-verify item 1's completion (`check_line_caps.sh` full-corpus `TARGETS` glob fix)
      against `check_line_caps_issues_subdir_full_corpus_glob_gap_2026_08_19.md` todo 1's own done-when — confirm a
      fresh full-corpus run lists `sports_all_vendor_honest_coverage_convergence_2026_08_07.md` as a HARD violation
      and `line_caps_baseline.yaml`'s `hard_count` reflects the newly-visible issue-doc violations without silently
      exceeding the shrinking-ratchet contract — then flip the source doc's own todo 1 checkbox citing the real
      commit SHA. Done-when: the source doc's todo 1 is `[x]` with independently-verified evidence, not a copied
      claim.
- [ ] [REVIEW] P2. Independently re-verify item 2's completion (the `# Epic: infrastructure_master` script-header
      sweep) against `epic_taxonomy_restructure_and_html_reconcile_2026_08_18.md`'s Phase 3 follow-up todo's own
      done-when — confirm `rg -c "^# Epic: infrastructure_master$" scripts/ tests/` returns 0 fleet-wide (or, if the
      sweep was itself split into further sub-batches per its own scale-note allowance, that every sub-batch is
      accounted for and none silently dropped) — then flip the source doc's own todo checkbox citing the real commit
      SHA(s). Done-when: the source doc's todo is `[x]` with independently-verified evidence.
- [ ] [DOC] P2. Once both items above reach their declared terminal state, run the standard six-step
      plan-completion-and-archival ritual on this finalize plan and the batch plan, including corpus-wide
      referrer-path repair. Done-when: the active-plan inventory has no orphan referrers to either archived path.

## Progress Log

- **2026-08-21 (na-eligibility-audit, infra tranche wave 2)**: authored alongside batch 1 after
  `check_finalize_plan_coverage.py`'s pre-commit hook rejected the batch plan for lacking a gated finalize companion
  (batch1 carries 2 open todos, so the script's documented single-todo carve-out does not apply — confirmed by
  reading the checker's own docstring before authoring this fix, not guessed). The plan is active and machine-gated
  via `depends_on` + `gate_on_depends: true`, following the exact pattern already proven by
  `infra_satellite_ao_dispatch_batch19_2026_08_18_finalize_2026_08_20.md` (same trigger, same shape).
