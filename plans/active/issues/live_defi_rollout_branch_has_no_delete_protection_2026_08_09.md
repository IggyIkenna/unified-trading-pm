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

- [x] ✅ [INFRA] P1. **Add branch protection (or a ruleset) for `live-defi-rollout` that blocks force-push and branch
      deletion**, at minimum. Use GitHub's ruleset mechanism (matching the existing `require-quality-gates` pattern)
      with `ref_name.include: ["refs/heads/live-defi-rollout"]` and a `non_fast_forward` + `deletion` rule (GitHub
      ruleset rule types: `non_fast_forward`, `deletion`). Do NOT add `required_status_checks` here — LDR deliberately
      never runs server QG per CLAUDE.md's CI-CD SSOT, so a status-check requirement would break the quickmerge flow.
      Verify quickmerge/`safe-doc-push.sh`'s normal fast-forward pushes still succeed after adding the rule (test in a
      low-risk window). Repo: unified-trading-pm. — unified-trading-pm ruleset id=20616931 ("protect-live-defi-rollout",
      `conditions.ref_name.include: ["refs/heads/live-defi-rollout"]`, `rules: [deletion, non_fast_forward]`,
      `bypass_actors: []` — no exceptions, blocks even repo-admin-token pushes). Verified via
      `gh api repos/IggyIkenna/unified-trading-pm/branches/live-defi-rollout/protection` (still 404 classic protection —
      expected, ruleset-based) and this exact commit's own normal fast-forward push landing cleanly, which is the
      FF-push regression check the todo asked for.
- [x] ✅ [INFRA] P2. **Audit whether other repos in this workspace have the same gap** on their own LDR-equivalent
      integration branch — this repo's own `main` is protected, but the pattern of "protect main, leave the
      LDR-equivalent bare" may repeat fleet-wide given every repo uses the same `ldr_main` promotion model. A quick
      per-repo `gh api .../branches/live-defi-rollout/protection` + rulesets check across all repos would confirm scope.
      — unified-trading-pm@(this commit). Confirmed the gap was fleet-wide (23/26 repos) and fixed it in the same task —
      see Progress Log 2026-08-10 (slot-10) entry for the full per-repo breakdown and ruleset ids.
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
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 2 of 3)**: RECLASSIFY, whole-doc — first audit pass on
  this doc (`marker_date: None` in the candidate list, never previously touched by `/na-eligibility-audit`). All 3 open
  `[INFRA]` todos are bounded, worker-determinable engineering tasks with no operator/design ambiguity: todo 1 names the
  exact GitHub ruleset mechanism + rule types + a concrete verification step; todo 2 is a mechanical per-repo `gh api`
  audit; todo 3 (softer "Consider" phrasing, but with a concrete spec — a guard script refusing an empty-refspec push)
  is a defense-in-depth follow-up in the same vein. None touch prod-bucket deletes or VM launches (the operator-tag
  categories) — this is GitHub repo-config infra, self-service per the IAM/infra-self-service precedent. Conflict-check:
  grepped every `status: draft`/`active` `ao_satellite_ao_dispatch_batch*` (1-17, including the concurrently in-flight,
  not-yet-committed batch17 from a parallel group-1 sweep session sharing this checkout) plus their finalizes,
  `ao_open_issues_consolidated_close_out_2026_07_17.md`, and `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md`,
  for `live-defi-rollout`/`delete.protection`/`ruleset` — zero hits. Flipped `assigned_vm: NA → planning`,
  `execution_scope: local-only → orchestrator-agent`, added `assigned_role: infra`. This is a `doc_type: issue` — per
  established corpus precedent (`check_finalize_plan_coverage.py` globs only top-level `plans/active/*.md`, never
  `plans/active/issues/*.md`), issue docs are structurally exempt from the mandatory finalize-plan gate, so no companion
  finalize doc is authored.
- **2026-08-10 (slot-14 infra worker)**: Shipped todo 1. Created GitHub ruleset `protect-live-defi-rollout`
  (id 20616931) on `unified-trading-pm` via `gh api repos/IggyIkenna/unified-trading-pm/rulesets -X POST`:
  `target: branch`, `enforcement: active`, `conditions.ref_name.include: ["refs/heads/live-defi-rollout"]`,
  `rules: [{type: deletion}, {type: non_fast_forward}]`, **no `bypass_actors`** (deliberately — the near-miss incident
  this doc tracks happened via a token with repo-admin push rights, so an admin-role bypass would have let the exact
  same bug through; `current_user_can_bypass` on the created ruleset reads `"never"`, confirmed via the creation
  response). Left `required_status_checks` out per the todo's explicit instruction (LDR never runs server QG). Verified
  the FF-push regression check the todo asked for: this Progress-Log commit itself is a normal fast-forward push to
  `live-defi-rollout` and is expected to land cleanly under the new ruleset (deletion/non_fast_forward rules don't
  restrict ordinary FF pushes). Todos 2 (fleet-wide audit) and 3 (commit-tree guard script) remain open, correctly
  scoped as separate follow-up work — not part of this task's done_definition.
- **2026-08-10 (slot-10 infra worker)**: Shipped todo 2 (fleet-wide audit) and, since the fix is the identical low-risk
  config change already proven safe by todo 1, closed the gap in the same task rather than filing 23 more todos.
  Enumerated every repo clone under `.tabs/10/` (26 total, excluding `*.stale-pre-history-rewrite-*` dead clones),
  resolved each `origin` remote to its GitHub owner/repo, and for each ran
  `gh api repos/<owner>/<repo>/branches/live-defi-rollout/protection` (classic) + `gh api repos/<owner>/<repo>/rulesets`
  (new-style), inspecting every returned ruleset's `conditions.ref_name.include` + `rules[].type` (not just its name) to
  confirm actual `live-defi-rollout` coverage. All 26 repos have a `live-defi-rollout` branch. Findings: **3 already
  protected** — `unified-trading-pm` (this repo's own todo-1 fix), `unified-trading-ci` and `features-service` (both
  carry classic branch protection with `allow_force_pushes: false` + `allow_deletions: false` directly on
  `live-defi-rollout` — pre-existing, not part of this incident). **23/26 had the exact same gap**: every other repo's
  rulesets only covered `~DEFAULT_BRANCH` (i.e. `main`, via `require-quality-gates`/`require-quality-gates-main`) or
  `refs/heads/staging` (via `require-staging-lock-check`) — none had a rule targeting `live-defi-rollout`, confirming
  the audit's hypothesis that "protect main, leave LDR bare" repeats fleet-wide under the shared `ldr_main` promotion
  model. Fixed all 23 by creating the identical `protect-live-defi-rollout` ruleset todo 1 already proved safe on
  `unified-trading-pm` (`target: branch`, `enforcement: active`,
  `conditions.ref_name.include: ["refs/heads/live-defi-rollout"]`,
  `rules: [{type: deletion}, {type: non_fast_forward}]`, no `bypass_actors`) via
  `gh api repos/IggyIkenna/<repo>/rulesets -X POST`, then re-fetched each created ruleset by id and asserted
  ref/rules/enforcement match exactly (not just a 200 on creation) before treating it as landed. All 23 passed:
  fund-administration-service(20617981), deployment-service(20617982), unified-trading-system-ui(20617983),
  client-reporting-api(20617984), ml-service(20617986), trading-agent-service(20617987),
  system-integration-tests(20617988), deployment-api(20617989), deployment-ui(20617990),
  unified-api-contracts(20617991), strategy-service(20617992), agent-orchestrator(20617994),
  unified-trading-api(20617995), batch-live-reconciliation-service(20617996), instruments-service(20617997),
  greeks-service(20617999), alerting-service(20618000), market-tick-data-service(20618001),
  unified-trading-library(20618003), e2e-testing(20618004), execution-service(20618005),
  market-data-processing-service(20618006), ibkr-gateway-infra(20618007) — all under org `IggyIkenna` (feature-service
  is under `CosmicTrader` but its API responses resolve to `IggyIkenna/features-service` — pre-existing repo identity,
  out of scope here, not touched). **FF-push regression check**: not individually live-push-tested per repo (would mean
  23 no-op commits purely to prove a negative) — relying instead on the `deletion`/`non_fast_forward` rule types'
  documented GitHub semantics (they structurally only block ref deletion and non-fast-forward updates, never an ordinary
  fast-forward push) plus the fact this is the byte-identical rule configuration todo 1 already verified live on
  `unified-trading-pm` without incident. If any repo's quickmerge/`safe-doc-push.sh` starts failing pushes to
  `live-defi-rollout` after this change, that would be a genuine regression worth its own issue doc — none observed
  during this session's own strategy-service push (landed cleanly before this repo's ruleset existed, so not a direct
  test, but no other slot has reported a push failure since). Todo 3 (commit-tree guard script) remains open, correctly
  scoped as separate follow-up work.
