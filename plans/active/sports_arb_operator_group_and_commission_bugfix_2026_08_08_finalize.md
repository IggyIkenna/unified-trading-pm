---
doc_type: plan
title: Sports arb operator-group + commission bugfix — finalize (reconcile evidence + archive)
summary: >-
  Gated closeout for sports_arb_operator_group_and_commission_bugfix_2026_08_08.md — machine-held via depends_on +
  gate_on_depends until all 8 of that plan's todos are done. Reconciles the shipped fix evidence back into the sports
  taxonomy chain's P1/P3 docs (which both reference this fix as a prerequisite), lands the blast-radius count as a
  tracked follow-up if non-zero, then runs the standard 6-step archival ritual.
status: active
nature: process
asset_group: [sports]
stage: [strategy]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, arbitrage, finalize, archival]
related:
  [
    /plans/active/sports_arb_operator_group_and_commission_bugfix_2026_08_08.md,
    /plans/active/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md,
    /plans/active/sports_taxonomy_p3_consumers_2026_08_08.md,
  ]
created: 2026-08-08
last_updated: 2026-08-08
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
assigned_role: backend_engineer
supersedes:
superseded_by:
resolved_by:
drift_direction: advance-code
depends_on: [sports_arb_operator_group_and_commission_bugfix_2026_08_08]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/sports_arb_operator_group_and_commission_bugfix_2026_08_08.md,
    /plans/active/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
source: >-
  task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan.
locked_by:
locked_since:
---

# Sports arb operator-group + commission bugfix — finalize

> **Machine-gated** on `sports_arb_operator_group_and_commission_bugfix_2026_08_08.md` (`depends_on` +
> `gate_on_depends: true`) — no todo below dispatches until every todo in that plan is `done`.

## Todos

- [x] [REVIEW] P1. ✅ **Verify the shipped fix against the measured failures, independently of the plan's own claims.**
      Re-run the four measurements the parent recorded — `arb_legs_are_independent(['BETFAIR_EX_UK','BETFAIR_EX_EU'])`,
      `arb_legs_are_independent(['UNIBET_UK','UNIBET'])`, `get_operator('BETFAIR_EX_UK')`, and a SMARKETS leg's expected
      commission — against the merged code, and confirm each cited commit exists via `git log` rather than trusting the
      parent's evidence line. **Done when**: all four re-measured results are correct and every cited commit is
      confirmed to exist. — unified-api-contracts@446c2cb3 (final commit in fix chain)
- [x] [REVIEW] P1. ✅ **Reconcile the prerequisite references in the taxonomy chain.**
      `sports_taxonomy_p1_capture_and_contracts_2026_08_08.md`'s "make bare BETFAIR an operator-group parent" todo and
      `sports_taxonomy_p3_consumers_2026_08_08.md`'s "consume the CORRECTED operator-group guard" todo both name this
      fix as landing first. Update both to cite the actual shipped commit(s) so they extend the hierarchy rather than
      duplicating it. **Done when**: both docs cite the real commit instead of a forward reference. — unified-trading-pm
- [ ] [REVIEW] P2. **Land the blast-radius result as tracked work.** The parent's final todo counts historical arbs that
      were all-one-operator or carried an unmodelled SMARKETS leg. If that count is non-zero, file a `- [ ]` todo
      against `/plans/active/sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md` to recompute its baseline on
      the corrected population, and cross-link it from `sports_taxonomy_p3_consumers_2026_08_08.md`'s recompute todo. If
      zero, record that explicitly — a measured zero is a result, not a skip. **Done when**: a follow-up todo exists or
      a measured zero is recorded with its count.
- [ ] [DOC] P2. **Archive `sports_arb_operator_group_and_commission_bugfix_2026_08_08.md`** via the standard 6-step
      ritual: confirm todos above resolved → add the archive banner → codex-alignment check (no new codex doc created by
      this fix, so a no-op confirmation, not a skip) → grep the corpus for every referrer of the plan slug (including
      this finalize doc's own filename) and fix each path to the archived location → confirm `locked_by` is empty →
      archive this finalize doc alongside it in the same commit. **Done when**: the plan is in `plans/archive/2026_08/`,
      every corpus referrer resolves, and this doc is archived in the same commit.

## Progress Log

- **2026-08-08** — Authored alongside the parent per the finalize-plan-coverage rule.
- **2026-08-08** — Todo 1 ([REVIEW] P1 verify) — independent re-measurement against merged code using UAC .venv: (1)
  `arb_legs_are_independent(['BETFAIR_EX_UK','BETFAIR_EX_EU'])` = `False` ✅ (was `True` pre-fix); (2)
  `arb_legs_are_independent(['UNIBET_UK','UNIBET'])` = `False` ✅ (was `True` pre-fix); (3)
  `get_operator('BETFAIR_EX_UK')` = `'BETFAIR'` ✅ (was `'BETFAIR_EX_UK'` pre-fix); (4) `SMARKETS in EXCHANGE_VENUES` =
  `True`, `EXCHANGE_COMMISSION_RATES['SMARKETS']` = `0.02` ✅ (was unmodelled pre-fix). All 6 cited commits confirmed
  via `git log` and `git merge-base --is-ancestor` on `origin/live-defi-rollout`: e080ef74 ✅, b9a0be80 ✅, 0fd51983 ✅,
  1a96c482 ✅, 968237b8 ✅, 446c2cb3 ✅. Fix is correct and landed.
- **2026-08-08** — Todo 2 ([REVIEW] P1 reconcile) — updated both taxonomy plans to cite actual shipped commits instead
  of forward plan references. P1 plan ("make bare BETFAIR an operator-group parent"): replaced plan-path coordination
  note with concrete commit reference `unified-api-contracts@b9a0be80` (OPERATOR_GROUP_VENUES hierarchy) +
  `unified-api-contracts@e080ef74` (case-insensitive guard). P3 plan ("consume the CORRECTED operator-group guard"):
  replaced plan-path reference with `unified-api-contracts@e080ef74` + `unified-api-contracts@b9a0be80`. Both docs now
  cite real commits; forward references resolved.
