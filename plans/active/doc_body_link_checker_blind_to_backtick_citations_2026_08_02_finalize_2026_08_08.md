---
doc_type: plan
title: check_doc_body_links.py backtick-citation blind spot — finalize
summary: >-
  Gated closeout for `doc_body_link_checker_blind_to_backtick_citations_2026_08_02.md` — machine-held via `depends_on` +
  `gate_on_depends: true` until both of that doc's todos (the codex/-prefix backtick-citation regex extension + the
  post-ship `/docs-reconcile` re-run) are done. Reconciles the shipped fix's real violation count against the
  round5-investigation estimate, confirms the baseline was seeded (not shipped zero-tolerance), then archives.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [docs-reconcile, quality-gates, retrieval-layer, close-out, archival, plan-hygiene]
related:
  [
    /plans/active/issues/doc_body_link_checker_blind_to_backtick_citations_2026_08_02.md,
    /plans/epics/agent_operating_framework_master.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/doc_body_link_checker_blind_to_backtick_citations_2026_08_02.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /plans/PLAN_FORMAT.md,
    /plans/active/task_template.md,
  ]
supersedes:
superseded_by:
depends_on: [doc_body_link_checker_blind_to_backtick_citations_2026_08_02]
gate_on_depends: true
source: >-
  /na-eligibility-audit round7 RECLASSIFY sweep, 2026-08-08 — required companion per `plans/active/task_template.md`
  §4's finalize-plan-coverage rule (every AO plan needs a paired gated finalize).
---

# check_doc_body_links.py backtick-citation blind spot — finalize

> **Machine-gated on `doc_body_link_checker_blind_to_backtick_citations_2026_08_02.md`** (`depends_on` +
> `gate_on_depends: true`) — the dispatcher will not queue any todo below until both of that doc's todos are `done`.

## Todos

- [ ] [REVIEW] P2. **Verify the shipped `codex/`-prefix backtick-regex extension's real violation count against the
      round5-investigation estimate (14 unresolved of 2,254 candidates).** Re-run the checker fresh against the live
      corpus post-ship; confirm the actual unresolved count lands in the estimated 6-8 genuine-fix range (excluding
      angle-bracket/ellipsis placeholders) rather than materially diverging. If it diverges, note why before treating
      the parent doc's estimate as validated. **Done when**: a real post-ship count is recorded here, sourced from a
      live run, not copied from the estimate. Repo: unified-trading-pm.
- [x] ✅ [REVIEW] P2. **Confirm the baseline was seeded via `--update-baseline` immediately after landing (not shipped
      zero-tolerance day one), matching how the original markdown-link checker itself was seeded 2026-07-23.** Check
      `scripts/quality_gates/doc_body_link_baseline.yaml` for a fresh `codex/`-prefix entry set consistent with the
      parent doc's own stated seeding intent. **Done when**: confirmed present, or the discrepancy is recorded. Repo:
      unified-trading-pm. — unified-trading-pm@d86597c6c3
- [ ] [DOCS] P2. **Archive the parent doc per the 6-step ritual, and only then.** Confirm zero open `- [ ]` todos
      remain; add the archival banner + set `status: complete`; grep the corpus for
      `doc_body_link_checker_blind_to_backtick_citations_2026_08_02` and repoint every referrer (the 5 digest-only docs
      identified at reclassify time: `ag_closeout_audit_rollout_2026_07_25.md`,
      `ao_satellite_ao_dispatch_batch3_2026_07_31.md`, `cross_cutting_consolidated_closeout_2026_07_25.md`,
      `infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md`, `tradfi_phase_d_terminal_gate_2026_07_24.md`, plus
      any new ones found live); clear any lock if set (confirm rather than assume). Then physically move the parent doc
      under `plans/archive/2026_08/`. **Done when**:
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci     --no-regen` is 0 hard, `check_reference_paths.py` shows
      no NEW dangling reference above its baseline, and `regenerate_active_plan_inventory.py` reports 0 orphans for this
      doc. Repo: unified-trading-pm.

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (6-step ritual) ·
`/codex/11-project-management/cross-reference-path-convention.md` · `plans/PLAN_FORMAT.md` ·
`plans/active/task_template.md` §4 (finalize-plan-coverage rule)

## Progress Log

- **2026-08-08**: Drafted alongside the parent doc's `na-eligibility-audit round7 RECLASSIFY` flip from
  `assigned_vm: NA` to `planning`. `status: active` immediately (not `draft`) — machine-held from actually dispatching
  via `depends_on` + `gate_on_depends: true` until the parent doc's 2 todos are done.
