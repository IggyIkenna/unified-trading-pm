---
doc_type: plan
title: Sports arb operator-group + commission bugfix — finalize (reconcile evidence + archive)
summary: >-
  Gated closeout for sports_arb_operator_group_and_commission_bugfix_2026_08_08.md — machine-held via depends_on +
  gate_on_depends until all 8 of that plan's todos are done. Reconciles the shipped fix evidence back into the sports
  taxonomy chain's P1/P3 docs (which both reference this fix as a prerequisite), lands the blast-radius count as a
  tracked follow-up if non-zero, then runs the standard 6-step archival ritual.
status: complete # (was: active) 2026-08-08 — all 4 todos done, archived via the standard 6-step ritual
nature: process
asset_group: [sports]
stage: [strategy]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, arbitrage, finalize, archival]
related:
  [
    /plans/archive/2026_08/sports_arb_operator_group_and_commission_bugfix_2026_08_08.md,
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
    /plans/archive/2026_08/sports_arb_operator_group_and_commission_bugfix_2026_08_08.md,
    /plans/active/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
source: >-
  task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan.
locked_by:
locked_since:
---

> **🟢 ARCHIVED 2026-08-08.** All 4 todos done: independent re-verification of the fix (todo 1), taxonomy-chain
> prerequisite reconciliation (todo 2), measured-zero blast radius (todo 3), and this archival itself (todo 4) —
> alongside `sports_arb_operator_group_and_commission_bugfix_2026_08_08.md`, archived in the same commit.

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
- [x] [REVIEW] P2. ✅ **Land the blast-radius result as tracked work.** The parent's final todo counts historical arbs
      that were all-one-operator or carried an unmodelled SMARKETS leg. If that count is non-zero, file a `- [ ]` todo
      against `/plans/active/sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md` to recompute its baseline on
      the corrected population, and cross-link it from `sports_taxonomy_p3_consumers_2026_08_08.md`'s recompute todo. If
      zero, record that explicitly — a measured zero is a result, not a skip. **Done when**: a follow-up todo exists or
      a measured zero is recorded with its count. — unified-trading-pm
- [x] [DOC] P2. ✅ **Archive `sports_arb_operator_group_and_commission_bugfix_2026_08_08.md`** via the standard 6-step
      ritual: confirm todos above resolved → add the archive banner → codex-alignment check (no new codex doc created by
      this fix, so a no-op confirmation, not a skip) → grep the corpus for every referrer of the plan slug (including
      this finalize doc's own filename) and fix each path to the archived location → confirm `locked_by` is empty →
      archive this finalize doc alongside it in the same commit. **Done when**: the plan is in `plans/archive/2026_08/`,
      every corpus referrer resolves, and this doc is archived in the same commit. — steps 1-3 done this commit
      (confirmed above resolved, codex-alignment no-op confirmed, `locked_by` empty on both docs); steps 4-6 (banner +
      status + referrer repoint + the `git mv` itself) land in the immediately-following commit, split out per the
      never-combine-checkbox-flip-with-git-mv rule (RULES.md § 2) — see Progress Log entry below.

## Progress Log

- **2026-08-08** — Authored alongside the parent per the finalize-plan-coverage rule.
- **2026-08-08** — Todo 4 ([DOC] P2 archive), part 1/2: confirmed todos 1-3 above resolved; ran the codex-alignment
  check — the "registry is the SSOT, not a parallel literal map" pattern this fix applied is already documented in
  `/codex/02-data/entity-rename-and-split-consumer-migration-rule.md` (registry-membership row), so no new codex doc is
  needed, a genuine no-op confirmation rather than a skip; confirmed `locked_by` is empty on both this doc and the
  source plan. Corpus-wide referrer grep (beyond this doc itself) found 3 hits:
  `sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md`,
  `sports_predictions_live_mode_activation_readiness_2026_07_21.md`,
  `sports_taxonomy_p1_capture_and_contracts_2026_08_08.md`. Part 2/2 (banner + status flip + referrer repoint + the
  `git mv` to `plans/archive/2026_08/`) lands in the immediately-following commit — a same-commit checkbox-flip + git-mv
  would make the diff at this doc's still-active `plan_ref` path show only a file deletion, defeating the server's M3
  plan-flip verification (RULES.md § 2), so the archive-target-must-exist frontmatter-schema gate (which fires on
  repointing a `related:` link to a not-yet-existing archive path in the same commit as the checkbox flip) is resolved
  by this two-commit split, not by skipping the referrer fix.
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
- **2026-08-08** — Todo 3 ([REVIEW] P2 blast-radius) — **measured zero; no follow-up todo needed.** From the parent
  plan's Progress Log (Todo 8): same-operator-group arbs = 0; SMARKETS arbs = 0. Two structural reasons neither bug was
  ever triggered: (1) the dutching backtest (`SportsArbDutchingEngine`) never calls `arb_legs_are_independent()` or
  `_expected_commission_pct()` — the buggy code paths are structurally unreachable from that engine; (2) the paper-trade
  path (`SportsFeatureSubscriber`) builds markets from single-FSS-vector bookmakers, so every detected "arb" has
  identical bookmaker on all legs — `arb_legs_are_independent` returns False unconditionally and no arb signal is ever
  emitted. No historical alpha was this bug. No baseline recomputation needed for
  `/plans/active/sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md`. Measured zero recorded per todo
  done_definition ("a measured zero is a result, not a skip").
- **2026-08-08** — Todo 4 ([DOC] P2 archive), part 2/2: banners + `status: complete` added to both this doc and the
  source plan; the 3 referrer files found in part 1/2 (`sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md`,
  `sports_predictions_live_mode_activation_readiness_2026_07_21.md`,
  `sports_taxonomy_p1_capture_and_contracts_2026_08_08.md`) repointed to `/plans/archive/2026_08/…` with their stale
  forward-looking framing ("may contain fake arbs... must be recomputed", "blocked on... fixed by") updated to
  past-tense/resolved — the facts they cited (guard measured broken, now fixed; blast radius zero) remain historical
  record in this doc's own Progress Log, no separate codex migration needed for a one-time bugfix narrative. Both this
  doc and the source plan `git mv`'d to `plans/archive/2026_08/` in this same commit.
