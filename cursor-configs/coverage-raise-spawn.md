# Coverage-Raise Spawn Prompt Template

> **Phase 7 deliverable** of `deployment_and_qg_strategy_implementation_2026_05_13.md` (P1). Paste this into the spawn
> prompt for any sub-agent tasked with raising coverage on a leaf service. One sub-agent per repo; spawn N in parallel
> via a single message with N `Task` tool uses.

---

## Required preamble (paste FIRST in every spawn prompt)

```
Before any action, read /Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md and follow ALL rules strictly. In particular:
  - Commit + push + flip plan checkboxes in the same agent turn (HARD RULE)
  - Use --no-verify only when prek auto-restore symptoms observed (Foot-gun #4)
  - Never touch foreign-dirty / untracked files in dep repos
  - quality-gates.sh is the only valid test runner (never `pytest` directly)
```

---

## Per-spawn parameters

Replace ALL `<...>` placeholders before sending:

```
REPO              = <repo name, e.g. features-service>
WORKTREE_PATH     = <.tabs/<N>/<repo> per per-tab-worktree convention>
COVERAGE_TARGET   = <target % from unified-trading-pm/scripts/quality_gates/coverage_targets.yaml>
CURRENT_BASELINE  = <current % from `quality_gates_snapshot` or local `pytest --cov` run>
SURFACES_IN_SCOPE = <comma-separated list of glob_patterns this sub-agent owns>
PLAN_FLIP_TARGET  = <path:line in active plan to flip on completion>
```

---

## Body (paste after the preamble + parameters)

```
You are a coverage-raise sub-agent for $REPO at $WORKTREE_PATH on branch
tab/ikennaigboaka/<slot-N> (per-tab-worktree isolation per
/codex/05-infrastructure/per-tab-worktrees.md).

GOAL: raise per-surface coverage to ≥ $COVERAGE_TARGET on the surfaces in
$SURFACES_IN_SCOPE without lowering coverage anywhere else.

BOUNDED WORK CONTRACT:
  1. cd $WORKTREE_PATH; git fetch; git status. If anything dirty that you
     don't own, STOP and report — that's another slot's WIP.
  2. Run `bash scripts/quality-gates.sh` once for a clean baseline. Save
     coverage.xml.
  3. Compute current coverage on $SURFACES_IN_SCOPE via fnmatch over
     coverage.xml (mimic
     unified-trading-pm/scripts/quality_gates/check_coverage_targets.py).
  4. Identify per-file gap: files in scope with <70% line coverage are
     priority-1; >70% but <$COVERAGE_TARGET are priority-2.
  5. For each priority-1 file:
       a. Read the file + its existing tests.
       b. Write per-branch unit tests covering: happy path, every public
          error branch, every fail-loud assertion. Use existing fixtures
          + parametrize where possible.
       c. Run tests; iterate until green.
       d. Re-run quality-gates.sh; confirm coverage went UP on this file
          and did NOT regress elsewhere.
       e. Commit + push to tab/ikennaigboaka/<slot-N> as
          `test($REPO): raise <file> coverage <old>%->\<new>% (Phase 8.B)`.
       f. After each commit: git fetch origin live-defi-rollout; if behind,
          stash any foreign-dirty files + rebase + pop + push.
  6. When $SURFACES_IN_SCOPE all hit $COVERAGE_TARGET, run
     `bash unified-trading-pm/scripts/quality_gates/check_coverage_targets.py --repo $REPO`
     to confirm. Then flip the plan checkbox at $PLAN_FLIP_TARGET in the
     SAME agent turn as the last test-coverage push.
  7. Final report (one paragraph): which files moved + old/new % per file +
     final per-surface aggregate + plan-flip commit SHA.

CONSTRAINTS:
  - DO NOT touch files outside $SURFACES_IN_SCOPE — other sub-agents may
    be raising adjacent surfaces in the same repo concurrently.
  - DO NOT mock the database or external services beyond what existing
    fixtures already mock. Real cassette / @mock_aws / @mock_gcp only.
  - DO NOT lower any global QG threshold to make tests pass. Threshold
    bumps are operator decisions (per CLAUDE.md).
  - DO NOT add new modules / classes / abstractions. Tests against existing
    public surface only.
  - DO NOT use `# type: ignore` to silence basedpyright. Fix the type or
    leave the test out.
  - Use --no-verify on commits ONLY when prek auto-restore symptoms
    appear in the output ("Restored working tree changes from
    .../prek/patches/").

SUCCESS CRITERION:
  ✅ check_coverage_targets.py shows all $SURFACES_IN_SCOPE ≥ $COVERAGE_TARGET
  ✅ quality-gates.sh full-suite passes
  ✅ Plan checkbox at $PLAN_FLIP_TARGET flipped in same agent turn as last
     code commit
  ✅ Report includes per-file before/after deltas + final plan-flip SHA

BOUNDED COST: stop at 4 hours of wall clock or 30 test files added,
whichever first. If still under target at that point, file an issue doc
at plans/active/issues/coverage_<REPO>_<surface>_<date>.md with: files
still under target, what made them resistant, recommended next step.
```

---

## How to spawn N sub-agents in parallel

Use a single message with N `Task` tool uses. Example for 3 leaf services in parallel:

```
Task #1: REPO=features-service           SURFACES_IN_SCOPE=src/features/calculators/*
Task #2: REPO=execution-service          SURFACES_IN_SCOPE=src/execution/error_classification/*
Task #3: REPO=strategy-service           SURFACES_IN_SCOPE=src/strategy/archetypes/*
```

Each Task is a fresh sub-agent — paste the preamble + parameters + body in full into each prompt. Do NOT assume
cross-task shared state.

---

## Per-tab-worktree discipline (HARD RULE)

Sub-agents MUST operate in `.tabs/<N>/<repo>/` worktrees (per
[per-tab-worktrees.md](/codex/05-infrastructure/per-tab-worktrees.md)). The spawn prompt above uses `$WORKTREE_PATH` for
this. Bootstrap:

```bash
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --init --slots 8
# or, for a specific slot:
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --add-slot 9
```

Without per-tab worktrees, multiple sub-agents running against the same root `<repo>/` directory will contend on the
index — basedpyright cache thrash, stash collisions, and lost commits. This has bitten this workspace before; DO NOT
skip the worktree step even for "quick" spawns.

---

## Composes with

- [SUB_AGENT_MANDATORY_RULES.md](SUB_AGENT_MANDATORY_RULES.md) — paste in preamble
- [coverage_targets.yaml](../scripts/quality_gates/coverage_targets.yaml) — surface→target map
- [check_coverage_targets.py](../scripts/quality_gates/check_coverage_targets.py) — ratchet
- [per-tab-worktrees.md](/codex/05-infrastructure/per-tab-worktrees.md) — worktree bootstrap
- [deployment_and_qg_strategy_implementation_2026_05_13.md](../plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md)
  — Phase 7 + 8
