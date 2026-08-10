---
doc_type: plan
title: Sports/predictions Group-C execution-alpha backtest harness — finalize
summary: >-
  Gated closeout for `sports_group_c_execution_backtest_harness_2026_07_21.md` — machine-held via `depends_on` +
  `gate_on_depends: true` until all 5 of that plan's implementation todos are done. Retroactive-reclassification
  finalize (na-eligibility-audit pattern (b), not a fresh satellite-batch carve-out): reconciles evidence for the CLI
  wiring + `SportsMatchingEngine` deletion + hermetic test, resolves the one remaining judgment call the 2026-08-08
  operator ruling didn't cover (docs/BACKTESTS.md verification-surface placement) via existing-sibling precedent, then
  runs the standard archival ritual.
status: active
nature: process
asset_group: [sports, prediction]
stage: [execution]
repos: [execution-service, unified-trading-pm]
scope: [engineer, admin]
tags: [sports, predictions, backtest, execution, group-c, close-out, archival, reclassification, na-audit]
related:
  [
    /plans/active/sports_group_c_execution_backtest_harness_2026_07_21.md,
    /plans/active/sports_predictions_live_mode_activation_readiness_2026_07_21.md,
    /plans/epics/sports_master.md,
    /codex/04-architecture/backtest-groups.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-10"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [sports_group_c_execution_backtest_harness_2026_07_21]
gate_on_depends: true
sequential: true
source: >-
  na-eligibility-audit sports-tranche round7 RECLASSIFY sweep, 2026-08-08 — required companion per
  `plans/active/task_template.md` §4's finalize-plan-coverage rule (every AO plan needs a paired gated finalize) and
  `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §1(b)'s retroactive-reclassification
  naming convention (`{original-stem}_finalize_{today}.md`, status: active from the start since `gate_on_depends`
  already machine-holds every todo below).
context_scope:
  [
    /plans/active/sports_group_c_execution_backtest_harness_2026_07_21.md,
    /codex/04-architecture/backtest-groups.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /plans/active/sports_predictions_live_mode_activation_readiness_2026_07_21.md,
  ]
---

# Sports/predictions Group-C execution-alpha backtest harness — finalize

> **Machine-gated on `sports_group_c_execution_backtest_harness_2026_07_21.md`** (`depends_on` +
> `gate_on_depends: true`) — the dispatcher will not queue any todo below until all 5 implementation todos in that plan
> are `done`. `sequential: true` because todo 2 needs todo 1's evidence-verification pass finished, and todo 4
> (archival) must run last.

## Todos

- [ ] [REVIEW] P2. **Verify every one of the parent plan's 5 `- [x]` todos actually carries checkable evidence, not just
      a claim.** For each: if it cites a commit sha (the `run_sports_backtest` CLI wiring, the `SportsMatchingEngine`
      deletion, the `extract_sports_instrument` extractor, the fixture data-source wiring, the hermetic
      `execution_alpha_bps` test), confirm it's a real ancestor of `execution-service`'s live branch
      (`git merge-base --is-ancestor <sha> origin/live-defi-rollout`). Specifically confirm: (a) `SportsMatchingEngine`
      is actually deleted (not just unwired) per the 2026-08-08 operator ruling's "no shims" instruction; (b)
      `run_sports_backtest` targets `L0Matcher`, not a resurrected `SportsMatchingEngine`; (c) the hermetic test
      genuinely asserts a non-trivial `execution_alpha_bps` (per `/codex/04-architecture/backtest-groups.md`'s Group-C
      output contract), not just that the CLI runs without erroring. **Done when**: every todo has an
      independently-reverified evidence line, and any todo whose evidence does not hold up is reopened with the
      discrepancy stated, not silently left `[x]`. Repo: execution-service.

- [ ] [REVIEW] P3. **Resolve the parent plan's one remaining judgment call — todo 5 (docs/BACKTESTS.md placement) — via
      existing-sibling precedent, not fresh judgment.** Check whether `docs/BACKTESTS.md` (or its replacement, if the
      "currently DEAD" finding in the parent plan is still accurate) lists the 3 existing domain runners
      (`run_cefi_backtest`/`run_tradfi_backtest`/`run_defi_backtest`) in a routine verification surface. If yes, add
      `run_sports_backtest` alongside them for consistency (default: match the established pattern, per this corpus's
      script/tooling-gap self-service precedent — an exact existing sibling precedent in the same repo needs no fresh
      operator judgment). If no such surface currently exists for any domain runner, leave it a manually-invoked one-off
      and record why. **Done when**: the placement decision is made and evidenced (either a real diff adding the entry,
      or a stated reason no surface exists to add it to), and the parent plan's todo 5 is flipped `[x]` with that
      evidence. Repo: execution-service.

- [ ] [REVIEW] P3. **Check whether this harness landing unblocks a downstream gate.**
      `/plans/active/sports_predictions_live_mode_activation_readiness_2026_07_21.md`'s Todo 5 (run a sports archetype
      through the promote-workflow CLI) is explicitly gated on "the Group-C execution-alpha harness landing." Confirm
      whether that todo is now unblocked (Group-B backtest also passing — check that plan's own prerequisites section)
      and, if so, leave a citation note there (do not flip its checkbox from this doc — that plan owns its own verdict).
      **Done when**: a citation note exists in the live-mode-readiness doc's Progress Log either way (still blocked on
      Group-B, or genuinely unblocked). Repo: unified-trading-pm.

- [ ] [TASK] P3. **Fix the review finding on `Any` + `# type: ignore` introduced in the harness commits**
      (`execution-service@893355cb` + `@7680d3f0d`).
      `execution_service/engine/backtest/actors/signal_driven_v3_base.py:88` ships
      `instruction_data: dict[str, dict[str, Any]]` (changed from `object` because Nautilus' msgspec `dec_hook` rejects
      `object` fields) — a nested-generic `Any` the QG Any-grep (`: Any|-> Any|[Any]`) does not catch, so the gate
      slipped green. Replace it with a typed shape (a `TypedDict`/Pydantic model, or `dict[str, dict[str, Unknown]]` if
      that round-trips) and VERIFY Nautilus msgspec serialization still round-trips for the instruction values (int
      direction, float benchmark_price, NaN TP/SL placeholders). Also remove the 2 blanket `# type: ignore` in
      `tests/unit/cli/test_sports_backtest_exec_alpha.py:74,78` (workspace-wide ban, STEP 5.24) — prefer a targeted
      narrow ignore or a typed fix. **Done when**: no `Any` remains in the production file, the test has no blanket
      `# type: ignore`, QG is green, and the hermetic exec-alpha test still passes. Repo: execution-service. In order:
      (1) confirm zero open `- [ ]` todos remain (all 5, post-verification above); (2) add the archival banner + set
      `status: complete`; (3) confirm no codex doc needs an update (this plan didn't introduce a new pattern beyond the
      existing cefi/tradfi/defi domain-runner shape, so likely none — verify, don't assume); (4) update every referrer's
      path corpus-wide — grep for `sports_group_c_execution_backtest_harness_2026_07_21` and repoint each hit (including
      `sports_predictions_live_mode_activation_readiness_2026_07_21.md`'s `related:` list and prerequisites section) to
      the archived path (leading-slash, repo-root-relative); (5) clear the lock if any was set (confirm rather than
      assume — none is expected here); (6) run `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci     --no-regen` and
      `check_reference_paths.py` to confirm no new dangling reference above baseline. Then physically move the parent
      plan under `plans/archive/2026_08/`. **Done when**: the hygiene sweep is 0 hard and
      `regenerate_active_plan_inventory.py` reports 0 orphans for this doc. Repo: unified-trading-pm.

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (6-step ritual) ·
`/codex/11-project-management/cross-reference-path-convention.md` ·
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` (retroactive-reclassification naming +
conflict-check protocol this finalize doc follows) · `/codex/04-architecture/backtest-groups.md` (Group-C output
contract) · `plans/active/task_template.md` §4 (finalize-plan-coverage rule)

## Progress Log

- **2026-08-08 (na-eligibility-audit, sports tranche, round7 RECLASSIFY sweep)**: Drafted alongside
  `sports_group_c_execution_backtest_harness_2026_07_21.md` when that plan was flipped from `assigned_vm: NA` to
  `planning`. `status: active` immediately (not `draft`) — machine-held from actually dispatching via `depends_on` +
  `gate_on_depends: true` until the parent plan's 5 todos are done, mirroring the
  `defi_compute_gcp_migration_2026_08_08_finalize_2026_08_08.md` precedent for a self-contained (non-batch) plan's
  finalize sibling.

- **2026-08-10 (main agent, routing review finding)**: Review surfaced a craft/standards finding on the harness commits
  (`execution-service@893355cb` + `@7680d3f0d`): `signal_driven_v3_base.py:88` ships `dict[str, dict[str, Any]]` (a
  nested-generic `Any` the QG Any-grep misses, so the gate slipped green) + 2 blanket `# type: ignore` in
  `tests/unit/cli/test_sports_backtest_exec_alpha.py:74,78`. Not done-blocking (hermetic `execution_alpha_bps` test
  itself verified good) — routed as a new `[TASK] P3` todo above. Slot 19 (author) is killed; the todo is available for
  any worker.
