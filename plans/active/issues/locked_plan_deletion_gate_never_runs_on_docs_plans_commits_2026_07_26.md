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
assigned_vm: planning
source: [/plan-reconcile cross-cutting (autonomous, 2026-07-26)]
execution_scope: orchestrator-agent
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

- [x] [OPERATOR] P1. **Rule on the direction before any mechanism changes** — either (a) the lock is genuinely mandatory
      and the gate must move somewhere every plan-touching commit passes through, or (b) archiving a resolved+terminal
      locked doc is acceptable autonomously and CLAUDE.md's "ASK, never autonomous" wording should be narrowed to say
      what it really means. **Done when**: an operator answer is recorded in
      `/plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md` § 11. Not AO-eligible — this is a
      governance/authority call, not a determinable fact. **RULED (a) 2026-07-26** — mandatory; CLAUDE.md's own text is
      unambiguous ("ASK, never autonomous"), this isn't really a policy choice up for grabs, just an enforcement gap to
      close. See entry #11 for the recorded ruling.
- [x] ✅ [SCRIPT] P1. **Move the locked-plan check to the `commit-msg` prek stage, NOT `pre-commit`** — sharpened
      2026-07-26: `run_hygiene_sweep.sh --precommit` fires at the `pre-commit` stage (`.pre-commit-config.yaml` default
      stages `[pre-commit, commit-msg]`), which for a `git commit -m "..."` invocation runs BEFORE `.git/COMMIT_EDITMSG`
      is reliably populated with the message-to-be (that file is written at `prepare-commit-msg`, validated at
      `commit-msg` — `pre-commit` structurally cannot see it). The existing `conventional-pre-commit` hook already runs
      at `stages: [commit-msg]` for exactly this reason (see its entry in `.pre-commit-config.yaml`) — model the new
      check on THAT hook's stage, not on `run_hygiene_sweep.sh --precommit`. Add a `commit-msg`-stage check (new script
      or a new mode on an existing one) that: reads staged deletions via
      `git diff --cached --diff-filter=D --name-only -- 'plans/active/**/*.md'` (recursive — the current
      `quality-gates.sh` glob `'plans/active/*.md'` misses `issues/**` entirely, a second independent bug), reads
      `locked_by` from `HEAD:$file`, and reads the message from the `commit-msg` hook's own argument (`$1`, the path
      prek passes to a commit-msg hook — NOT `git log -1`, which reads the PREVIOUS already-made commit, a third bug).
      `.pre-commit-config.yaml` is templated (`scripts/pre-commit-templates/` + `rollout-pre-commit-configs.sh`) — check
      whether `plans/active/` is PM-specific enough that this hook only needs adding to PM's own copy (likely, since no
      other repo has a `plans/` tree) before deciding whether a fleet-wide rollout is needed. Keep the
      `quality-gates.sh` copy or delete it, but do not leave two divergent implementations. **Done when**: a test commit
      that deletes a fixture doc carrying `locked_by:` is BLOCKED without `[unlock-plan]` and PASSES with it,
      demonstrated with the real hook output pasted into this doc's Progress Log. — **DONE unified-trading-pm** (see
      Progress Log for shas + real hook output). **CORRECTION on the "second independent bug" claim above**: MEASURED
      (not assumed) against the real cited historical commit (`57ed9271c`) —
      `git diff --diff-filter=D --name-only 57ed9271c~1 57ed9271c -- 'plans/active/*.md'` lists
      `plans/active/issues/mtds_uac_adapter_contract_baseline_regression_2026_07_09.md` IDENTICALLY to the unfiltered
      deletion list. Git's default pathspec `*` crosses `/` (unlike a shell glob) — `'plans/active/*.md'` was ALREADY
      correct and already matched `issues/**`. The `**` variant this todo suggested is actually WRONG: measured 433
      matches vs 696 for the single-star form — `**` requires ≥1 subdirectory, silently EXCLUDING files directly in
      `plans/active/`. Kept the proven-correct `plans/active/*.md` pattern; see the correction comment in
      `scripts/hooks/check-locked-plan-deletion.sh`. Only genuine bugs #2 (routing — the actual root cause) and #3
      (`git log -1` reads the wrong commit) needed fixing.
- [x] ✅ [SCRIPT] P2. **Fix the `git log -1` commit-message read** in `scripts/quality-gates.sh:410` regardless of which
      direction (a)/(b) is chosen, or delete the block if it moves. **Done when**: the check reads the message of the
      commit being created, proven by a pre-commit run that sees a `[unlock-plan]` tag typed for THAT commit. — **DONE**
      resolved via deletion (the sanctioned P1 path): the `quality-gates.sh:406-422` block is removed entirely (dead
      code for its own use case, and now fully superseded by the commit-msg hook, which reads `$1` — the real
      message-to-be — not `git log -1`). Proven by the same P1 verification: the commit-msg hook correctly read
      `[unlock-plan]` from the message of the commit BEING CREATED (see Progress Log real hook output).
- [ ] [DOC] P2. **Retro-clean the one doc this already affected** — `plans/archive/issues/`
      `mtds_uac_adapter_contract_baseline_regression_2026_07_09.md` still carries `locked_by: live-defi-rollout` while
      archived; clear the lock (or restore the doc to `plans/active/` if the operator rules the archival was premature).
      **Done when**: the archived doc has an empty `locked_by:` and a dated note recording which way it was ruled.

## Codex SSOTs (read before touching a todo)

`/codex/11-project-management/` (archival ritual + issue-doc lifecycle), `/codex/06-coding-standards/quality-gates.md`.

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-27** — P1+P2 shipped (slot-6). New `scripts/hooks/check-locked-plan-deletion.sh` (commit-msg stage, reads
  `$1` per prek's commit-msg contract, `plans/active/*.md` pathspec) wired into `.pre-commit-config.yaml` (PM root + the
  `docs.pre-commit-config.yaml` template, script self-guards as a no-op outside a `plans/` tree) with
  `stages: [commit-msg]`. Deleted the dead `scripts/quality-gates.sh:406-422` block (P2, resolved via deletion).
  End-to-end verified with a disposable fixture doc
  (`plans/active/issues/_test_fixture_locked_plan_deletion_gate_2026_07_27.md`, `locked_by: test-fixture-verification`),
  real `prek`-driven `git commit` runs, output captured verbatim then the fixture + its throwaway commits discarded
  (`git reset --mixed` back past them — net-zero file diff, nothing shipped):

  ```
  # 1) ADD the locked fixture — hook must no-op (nothing deleted yet):
  Locked-plan deletion gate (blocks archiving a locked_by plan without [unlock-plan])..................................Passed

  # 2) DELETE it WITHOUT [unlock-plan] — must BLOCK:
  Locked-plan deletion gate (blocks archiving a locked_by plan without [unlock-plan])..................................Failed
  - hook id: check-locked-plan-deletion
  - exit code: 1

    ❌ BLOCKED: plans/active/issues/_test_fixture_locked_plan_deletion_gate_2026_07_27.md is locked by 'test-fixture-verification'.
       To delete a locked plan, include [unlock-plan] in your commit message.
       This prevents agents from accidentally removing plans that are actively being implemented.

  # 3) Same delete, commit message now carries [unlock-plan] — must PASS:
  Locked-plan deletion gate (blocks archiving a locked_by plan without [unlock-plan])..................................Passed
  [live-defi-rollout 18eba1ecb] test: delete locked fixture WITH unlock tag [unlock-plan]
  ```

  Also disproved (not assumed) the todo's own "`plans/active/*.md` misses `issues/**`" claim by testing the exact
  historical commit it cites — see the P1 checkbox note above. P3 (retro-clean the one already-affected archived doc)
  left open — separate file, separate [DOC]-tagged todo, not this dispatch's scope.

- **2026-07-26** — Filed by `/plan-reconcile cross-cutting` (autonomous). Surfaced while parking the `[unlock-plan]` ask
  for `mtds_uac_adapter_contract_baseline_regression_2026_07_09.md`: mid-run, a concurrent escalation-driven remediation
  (`@57ed9271c`) archived that exact doc without the approval the park was waiting on. All four evidence items above
  were measured this pass, not inferred; the `git mv`-evades-`--diff-filter=D` hypothesis was tested and **refuted**
  before landing on the routing gap.
