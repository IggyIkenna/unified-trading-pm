---
doc_type: issue
title:
  "The locked-plan-deletion gate lives only in quality-gates.sh, which docs(plans): commits are explicitly exempt from —
  so a `locked_by:` plan can be archived with no [unlock-plan] approval"
summary: >-
  CLAUDE.md states plainly that "`locked_by:` blocks archival without `[unlock-plan]` (ASK, never autonomous)", and
  `scripts/quality-gates.sh:406-422` implements exactly that gate. But the gate is unreachable for the ONLY commit class
  that archives plans: CLAUDE.md's own QG-batching rule says "pure doc/plan-flip → prek only", so `quality-gates.sh`
  never runs for a `docs(plans):` archival commit, and the prek/pre-commit hook chain does not carry the check (verified
  by reading the hook output of a real `docs(plans):` commit — Prettier, gitleaks, whitespace, EOF, large files, merge
  conflicts, private key, line ending, Conventional Commit, slot identity, branch drift, plan-hygiene, ruff — no
  locked-plan check). Demonstrated live, not hypothesised: `unified-trading-pm@57ed9271c` ("plan_health gate
  auto-remediation — archive 11 terminal-status docs") archived
  `plans/active/issues/mtds_uac_adapter_contract_baseline_regression_2026_07_09.md`, which carries `locked_by:
  live-defi-rollout`, with no `[unlock-plan]` anywhere in the commit message and no block. The archived copy at
  `plans/archive/issues/` STILL carries `locked_by: live-defi-rollout` — archival-ritual step 6 ("clear lock") was also
  skipped. Net effect: the workspace's one explicit human "not yours" signal on a plan is advisory in practice while
  reading as mandatory in CLAUDE.md — an agent that honours it (as `/plan-reconcile` did, parking instead of archiving)
  is strictly slower than one that does not.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, quality-gates, governance, locked-plan, archival-ritual, prek]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
    /plans/active/issues/plan_quality_four_line_defense_architecture_2026_07_23.md,
  ]
created: 2026-07-26
parent_epic: plan_hygiene_master
assigned_vm: NA
source: [/plan-reconcile cross-cutting (autonomous, 2026-07-26)]
execution_scope: local-only
priority: P1
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
---

# The locked-plan-deletion gate never runs on the commits that archive plans

## The contradiction

| Side                     | Claim                                                                                                                                                                        | Location                                                           |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Rule (reads MANDATORY)   | "**Plan locking** `locked_by:` blocks archival without `[unlock-plan]` (ASK, never autonomous)"                                                                              | `cursor-configs/CLAUDE.md`, Plans § Estimate calibration paragraph |
| Gate (exists, real)      | `❌ BLOCKED: $plan_file is locked by '$LOCKED_BY'. To delete a locked plan, include [unlock-plan] in your commit message.`                                                   | `scripts/quality-gates.sh:406-422`                                 |
| Routing (defeats it)     | "**QG-sweep batching** — … **pure doc/plan-flip → prek only**"                                                                                                               | `cursor-configs/CLAUDE.md`, Git-discipline §                       |
| Observed (gate no-fires) | `docs(plans): plan_health gate auto-remediation — archive 11 terminal-status docs + fix 2 bare codex refs` archived a `locked_by:` doc with no `[unlock-plan]` and no block. | `unified-trading-pm@57ed9271c`                                     |

Both CLAUDE.md statements are individually correct. Composed, they make the gate dead code for its own use case: the
gate only ever executes under `quality-gates.sh`, and the archival commit class is the one class explicitly routed away
from `quality-gates.sh`.

## Evidence (measured this pass, 2026-07-26)

1. **The gate exists and looks right.** `scripts/quality-gates.sh:408` —
   `DELETED_PLANS=$(git diff --cached --diff-filter=D --name-only -- 'plans/active/*.md')`, then `:415` requires
   `[unlock-plan]` in the commit message when the deleted file's `HEAD:` frontmatter has a non-empty `locked_by`.
2. **The filter is NOT the problem** (ruling out the obvious `git mv`-shows-as-rename hypothesis):
   `git diff --name-status 57ed9271c~1 57ed9271c -- 'plans/active/*.md'` classifies every archived doc as **`D`**, not
   `R` — so `--diff-filter=D` would have matched. The gate simply never ran.
3. **The pre-commit chain does not carry the check.** The hook list that actually executed on a real `docs(plans):`
   commit this session: Prettier · gitleaks · trailing whitespace · end-of-file · yaml · toml · large files · merge
   conflicts · private key · mixed line ending · Conventional Commit · slot·host identity · branch drift · Plan hygiene
   (staged plans + codex + runbooks) · Ruff. No locked-plan gate. `run_hygiene_sweep.sh --precommit` likewise runs only
   frontmatter / schema / todo-format / conflict-markers / prettier-mangling / line-caps.
4. **The lock survived the archival.**
   `plans/archive/issues/mtds_uac_adapter_contract_baseline_regression_2026_07_09.md` still has
   `locked_by: live-defi-rollout` at line 28 alongside `status: resolved` — step 6 of the 6-step archival ritual ("clear
   lock") did not run either.

## Secondary defect in the same block (independent of the routing gap)

`scripts/quality-gates.sh:410` reads the commit message as `COMMIT_MSG=$(git log -1 --format=%B)`. Run pre-commit — the
documented usage ("**Quality gates BEFORE COMMIT** — the commit is the per-repo quality boundary") — `git log -1` is the
**previous** commit, so the check tests the wrong message: it can pass on an unrelated earlier `[unlock-plan]` and fail
a correctly-tagged commit that has not been written yet. Worth fixing in the same pass as whatever addresses the routing
gap, but note it is not what let `@57ed9271c` through (that commit never reached this code at all).

## Why this is P1, not cosmetic

`locked_by:` is the workspace's only explicit per-doc "a human is holding this" signal, and CLAUDE.md escalates it to a
HARD rule twice (Plans § and the `/plan-reconcile` skill's routing table: "**An explicit human signal**: `locked_by:` is
a person saying 'not yours' — `[unlock-plan]` is theirs to give"). Today a rule-following agent parks and waits while a
rule-unaware automation archives the same doc unblocked, in the same hour. That asymmetry teaches exactly the wrong
lesson, and it silently erodes the one guardrail that is supposed to be un-automatable.

## Todos

- [ ] [OPERATOR] P1. **Rule on the direction before any mechanism changes** — either (a) the lock is genuinely mandatory
      and the gate must move somewhere every plan-touching commit passes through, or (b) archiving a resolved+terminal
      locked doc is acceptable autonomously and CLAUDE.md's "ASK, never autonomous" wording should be narrowed to say
      what it really means. **Done when**: an operator answer is recorded in
      `/plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md` § 11. Not AO-eligible — this is a
      governance/authority call, not a determinable fact.
- [ ] [SCRIPT] P1. **If (a): move the locked-plan check into the pre-commit path** — add it to
      `scripts/plan-hygiene/run_hygiene_sweep.sh --precommit` (which already reads the staged set and already runs on
      every plan-touching commit via prek), reading the message from `.git/COMMIT_EDITMSG`/the `commit-msg` hook stage
      rather than `git log -1`, and covering `plans/active/**` including `issues/`. Keep the `quality-gates.sh` copy or
      delete it, but do not leave two divergent implementations. **Done when**: a test commit that deletes a fixture doc
      carrying `locked_by:` is BLOCKED without `[unlock-plan]` and PASSES with it, both demonstrated in the doc's
      Progress Log with the real hook output pasted.
- [ ] [SCRIPT] P2. **Fix the `git log -1` commit-message read** in `scripts/quality-gates.sh:410` regardless of which
      direction (a)/(b) is chosen, or delete the block if it moves. **Done when**: the check reads the message of the
      commit being created, proven by a pre-commit run that sees a `[unlock-plan]` tag typed for THAT commit.
- [ ] [DOC] P2. **Retro-clean the one doc this already affected** — `plans/archive/issues/`
      `mtds_uac_adapter_contract_baseline_regression_2026_07_09.md` still carries `locked_by: live-defi-rollout` while
      archived; clear the lock (or restore the doc to `plans/active/` if the operator rules the archival was premature).
      **Done when**: the archived doc has an empty `locked_by:` and a dated note recording which way it was ruled.

## Codex SSOTs (read before touching a todo)

`/codex/11-project-management/` (archival ritual + issue-doc lifecycle), `/codex/06-coding-standards/quality-gates.md`.

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-26** — Filed by `/plan-reconcile cross-cutting` (autonomous). Surfaced while parking the `[unlock-plan]` ask
  for `mtds_uac_adapter_contract_baseline_regression_2026_07_09.md`: mid-run, a concurrent escalation-driven remediation
  (`@57ed9271c`) archived that exact doc without the approval the park was waiting on. All four evidence items above
  were measured this pass, not inferred; the `git mv`-evades-`--diff-filter=D` hypothesis was tested and **refuted**
  before landing on the routing gap.
