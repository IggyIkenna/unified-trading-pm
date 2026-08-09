---
doc_type: issue
title: >-
  live-defi-rollout carries zero GitHub protection — a near-miss force-push-delete during a round-9 sweep worked out
  only because the bug was self-caught in the same turn
summary: >-
  While shipping round-9 satellite-extraction work, a scripting bug in a `git commit-tree` retry loop (an unset
  commit-message variable produced an empty ref) executed `git push origin :live-defi-rollout` — which deletes the
  remote branch. The agent caught it immediately via `git ls-remote`, restored the branch to its exact prior tip, and
  verified the log matched before retrying. Independently re-verified: `git ls-remote origin live-defi-rollout` and `git
  log origin/live-defi-rollout` both show a clean, continuous history with no gaps, duplicate SHAs, or orphaned commits
  — no data was actually lost. **But nothing structurally prevented that from being unrecoverable.** Checked both
  protection mechanisms: the classic branch-protection API returns 404 ("Branch not protected") for `live-defi-rollout`,
  and the one active ruleset (`require-quality-gates`, id 13647441) targets `ref_name.include: ["~DEFAULT_BRANCH"]` only
  — i.e. `main`, not `live-defi-rollout` — and its sole rule type is `required_status_checks`, which doesn't cover
  deletion or force-push at all. `live-defi-rollout` is the shared integration branch every quickmerge in this repo
  lands on and every concurrent agent pulls/rebases against directly — it is exactly the branch this workspace's own
  HARD RULE ("NEVER force-push a shared branch") is written to protect, and it currently has no GitHub-side backstop if
  that rule is ever violated (accidentally, via a bug like this one, or otherwise).
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [branch-protection, git-safety, live-defi-rollout, near-miss, github-rulesets, incident]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-09
author: claude-agent
parent_epic: agent_operating_framework_master
priority: P1
source: >-
  Discovered while independently verifying a round-9 na-eligibility-audit sweep agent's own incident report (it briefly
  force-deleted `live-defi-rollout` via a retry-loop bug, self-caught and restored in the same turn, no data lost).
  Main-session verification of the recovery surfaced the underlying structural gap.
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
assigned_role: infra
drift_direction: none
depends_on: []
locked_by:
resolved_by:
context_scope: [/codex/08-workflows/ci-cd-flow.md]
---

# `live-defi-rollout` has no delete/force-push protection

## What happened

A round-9 `na-eligibility-audit` sweep agent, working around severe shared-checkout write contention, built commits via
`git commit-tree` against `origin`'s HEAD directly (the documented workaround for this exact contention class). A bug in
its retry loop — an unset commit-message variable producing an empty ref — resulted in
`git push origin :live-defi-rollout` executing, which deletes the remote branch. The agent caught this immediately via
`git ls-remote`, restored the branch to its exact prior tip (`1b450b785c76800d0cd39d2a3ad95288b9e1eabd`), verified the
restored log matched exactly, and continued.

**Independently re-verified (main session, same day)**: `git ls-remote origin live-defi-rollout` resolves to a live SHA;
`git log --oneline -15 origin/live-defi-rollout` shows a clean, continuous, sensible commit history with no gaps or
duplicate/orphaned SHAs. No data was lost.

## The real finding: no GitHub-side backstop exists for this branch

- Classic branch-protection API: `gh api repos/IggyIkenna/unified-trading-pm/branches/live-defi-rollout/protection` →
  `404 Branch not protected`.
- Rulesets API: exactly one active ruleset (`require-quality-gates`, id `13647441`), but its
  `conditions.ref_name.include` is `["~DEFAULT_BRANCH"]` — i.e. it targets `main` only — and its `rules` array contains
  only `required_status_checks`. Neither covers `live-defi-rollout`, nor deletion/force-push at all, on any branch.

`live-defi-rollout` is the SSOT integration branch this entire workspace's multi-agent model depends on — every
`quickmerge.sh` lands here, every slot/worktree's `git pull --ff-only` tracks it directly, and CLAUDE.md's own HARD RULE
states "NEVER force-push a shared branch." That rule currently has no machine enforcement behind it for this specific
branch — it worked this time only because the bug was caught by the same agent, in the same turn, before any other
process observed the deleted state.

## Todos

- [ ] [INFRA] P1. **Add branch protection (or a ruleset) for `live-defi-rollout` that blocks force-push and branch
      deletion**, at minimum. Use GitHub's ruleset mechanism (matching the existing `require-quality-gates` pattern)
      with `ref_name.include: ["refs/heads/live-defi-rollout"]` and a `non_fast_forward` + `deletion` rule (GitHub
      ruleset rule types: `non_fast_forward`, `deletion`). Do NOT add `required_status_checks` here — LDR deliberately
      never runs server QG per CLAUDE.md's CI-CD SSOT, so a status-check requirement would break the quickmerge flow.
      Verify quickmerge/`safe-doc-push.sh`'s normal fast-forward pushes still succeed after adding the rule (test in a
      low-risk window). Repo: unified-trading-pm.
- [ ] [INFRA] P2. **Audit whether other repos in this workspace have the same gap** on their own LDR-equivalent
      integration branch — this repo's own `main` is protected, but the pattern of "protect main, leave the
      LDR-equivalent bare" may repeat fleet-wide given every repo uses the same `ldr_main` promotion model. A quick
      per-repo `gh api .../branches/live-defi-rollout/protection` + rulesets check across all repos would confirm scope.
- [ ] [INFRA] P3. **Consider hardening the `git commit-tree` fallback pattern itself** (documented in
      `SUB_AGENT_MANDATORY_RULES.md` as the recovery path for shared-checkout contention) — the specific bug here was an
      unset variable producing `git push origin :<branch>` instead of `git push origin <sha>:<branch>`. A small guard
      script wrapping this pattern (refuse to push if the local side of the refspec is empty/unset) would catch this
      class of bug before it reaches `git push`, independent of the branch-protection fix above (defense in depth — the
      two fixes address different layers).

## Progress Log

- 2026-08-09: Filed after independently verifying a round-9 sweep agent's self-reported near-miss (branch briefly
  force-deleted via a `git commit-tree` retry-loop bug, self-caught and restored same-turn, no data lost). The recovery
  itself was clean and correct; this doc tracks the underlying structural gap the incident revealed —
  `live-defi-rollout` has no GitHub-side deletion/force-push protection at all.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 2 of 3)**: RECLASSIFY, whole-doc — first audit pass
  on this doc (`marker_date: None` in the candidate list, never previously touched by `/na-eligibility-audit`). All 3
  open `[INFRA]` todos are bounded, worker-determinable engineering tasks with no operator/design ambiguity: todo 1
  names the exact GitHub ruleset mechanism + rule types + a concrete verification step; todo 2 is a mechanical
  per-repo `gh api` audit; todo 3 (softer "Consider" phrasing, but with a concrete spec — a guard script refusing an
  empty-refspec push) is a defense-in-depth follow-up in the same vein. None touch prod-bucket deletes or VM launches
  (the operator-tag categories) — this is GitHub repo-config infra, self-service per the IAM/infra-self-service
  precedent. Conflict-check: grepped every `status: draft`/`active` `ao_satellite_ao_dispatch_batch*` (1-17, including
  the concurrently in-flight, not-yet-committed batch17 from a parallel group-1 sweep session sharing this checkout)
  plus their finalizes, `ao_open_issues_consolidated_close_out_2026_07_17.md`, and
  `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md`, for `live-defi-rollout`/`delete.protection`/`ruleset` —
  zero hits. Flipped `assigned_vm: NA → planning`, `execution_scope: local-only → orchestrator-agent`, added
  `assigned_role: infra`. This is a `doc_type: issue` — per established corpus precedent
  (`check_finalize_plan_coverage.py` globs only top-level `plans/active/*.md`, never `plans/active/issues/*.md`), issue
  docs are structurally exempt from the mandatory finalize-plan gate, so no companion finalize doc is authored.
