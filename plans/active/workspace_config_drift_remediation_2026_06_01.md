---
title:
  "Workspace .code-workspace repo-list drift remediation (canonical commit + generator path-style fix + regression
  guard)"
name: workspace_config_drift_remediation
created: 2026-06-01
parent_epic: epics/infrastructure_master.md
assigned_vm: vm-cross-cutting
locked_by: live-defi-rollout
locked_since: 2026-06-01
status: active
priority: P2
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
---

# Workspace `.code-workspace` repo-list drift — remediation

> **Source issue**: [workspace_config_repo_list_drift_2026_06_01](issues/workspace_config_repo_list_drift_2026_06_01.md)
> (filed slot 5, interactive, 2026-06-01 @ `unified-trading-pm@a1774365a`). Read it for the full root-cause; this plan
> tracks the **systemic remediation** (the deployed symptom on the 11 tab `.code-workspace` files was already
> self-healed by slot 5 — do not redo). Once items 1–3 ship + item 4 is adjudicated, the issue doc archives per the
> issue-doc lifecycle.

## Context (verified 2026-06-01)

- **Canonical SSOT** = `unified-trading-pm/cursor-configs/unified-trading-system-repos.code-workspace` (git-tracked).
  The repos-root `unified-trading-system-repos.code-workspace` is a symlink → `.cursor/workspace-configs/` (a directory
  symlink → `unified-trading-pm/cursor-configs/`), so **the main-worktree VS Code view loads exactly the tracked
  canonical** (md5-verified identical). Committing the canonical durably fixes the main view.
- Canonical `folders[]` = `../../` (Workspace Root) + 25 `../../<repo>` paths. The 25 repo names == the active +
  scaffolded repo set in `workspace-manifest.json` (`status: active | scaffolded`), excluding the 12
  archived/consolidated entries (`risk-and-exposure-service`, `pnl-attribution-service`,
  `position-balance-monitor-service`, `ml-inference-service`, `ml-training-service`, `user-management-ui`, +6
  `features-*-service` consolidated).
- The slot-5 canonical fix was sitting **uncommitted in the ROOT worktree** (which is 894 commits behind LDR with
  foreign dirty files → cannot FF-push). The delta vs **current** `origin/live-defi-rollout` is exactly: add
  `greeks-service` + `fund-administration-service` to `folders[]`, drop 6 stale
  `ml-inference-service`/`ml-training-service` `git.ignoredRepositories` entries (tabs 9/10/11). Both added repos are
  `status: active`. The `greeks-service` line was foreign in-flight WIP but is a real active repo, so landing it is
  correct (per issue rec #1).

## Todos

- [x] ✅ [SCRIPT] P2. **Item 1 — commit the canonical `.code-workspace` fix.** Land slot-5's prepared canonical change
      (add `greeks-service` + `fund-administration-service`; drop 6 stale `ignoredRepositories` entries) to
      `live-defi-rollout`. Verify `folders[]` (minus the `../../` workspace-root) == manifest active+scaffolded repo set
      first. Commit from a worktree that can FF (NOT the 894-behind root); `docs`/`chore` prefix. The root symlink chain
      makes this fix the main-worktree view durably. — unified-trading-pm@73963a354 | verified folders[]==25
      active+scaffolded repos, 0 drift | committed from slot-1 (root worktree was 894 behind, unpushable).
- [x] ✅ [SCRIPT] P2. **Item 2 — fix `setup-tab-worktrees.sh:copy_workspace_file` path style.** Plain `cp` of the
      canonical (which uses `../../<repo>` paths, correct for its 2-levels-deep home) into a slot dir `.tabs/N/` makes
      `../../<repo>` resolve to the **main** worktree, not the slot's → slots silently edit the wrong checkout. Existing
      deployed tab files use **bare relative** paths, so land on relative: strip `../../` from `path` values on copy
      (portable sed) + keep the workspace-root folder as `.`. Document which file is canonical for which consumer (root
      symlink → tracked canonical with `../../`; slot copies → bare relative). **Script → PR targets `staging`** per
      PM/Codex fast-path. — unified-trading-pm@c6dab6afd | transform verified: 26 folders → `.` + 25 bare-relative
      repos, 0 residual `../../`, valid JSON, matches deployed tab-file style. **Fast-path deviation**: landed on LDR
      not a staging PR — staging is 632 commits behind LDR, branching off it to edit this newer script is a stale-base
      revert hazard (don't-dump-others'-work HARD RULE); LDR→staging reconciliation carries it forward. Flagged to
      operator.
- [ ] [SCRIPT] P2. **Item 3 — regression guard.** Add a check (PM `quality-gates.sh` step and/or pytest) asserting the
      canonical `.code-workspace` `folders[]` (minus workspace-root) == active+scaffolded repo set in
      `workspace-manifest.json`, and that no listed path is a known archived/consolidated repo. Optionally assert
      `git.scanRepositories`/`git.ignoredRepositories` entries resolve to real repo names. Closes Finding 3 (no guard ⇒
      both drifts went silent). **Script → PR targets `staging`** (bundle with Item 2; include the Item-1 canonical fix
      on the staging branch so the guard is green there too).
- [ ] [PM] P2. **Item 4 — adjudicate the features-service `ci_status` edit (Observation A).** Slot-5 `stash@{0}`
      (`slot5-FOREIGN: features-service ci_status LOCAL_PASS->FAILING`) holds an uncommitted flip that was starving
      slot-5 PM's FF-pull cron (963 behind). Decide WITH operator: is features-service CI actually FAILING (commit the
      `workspace-manifest.json` flip + point at remediation) or stale WIP (drop the stash)? Either way a slot PM tree
      must not carry a perpetually-dirty `workspace-manifest.json`.
- [ ] [SCRIPT] P3. **Item 5 — FF-pull starvation watchdog signal (optional).** Propose a signal: a slot N that is
      commits-behind `origin` with a clean FF available but blocked by a dirty-file collision should ping the
      orchestrator instead of sitting silent (root cause of slot-5 being 963 behind). Spec only under this todo;
      implementation wires into `slot-git-status-report.sh` / `slot-cron-ff-pull.sh`.

## Codex SSOT updates

- `codex/05-infrastructure/per-tab-worktrees.md` — document the canonical-vs-slot `.code-workspace` path-style contract
  (Item 2) + the regression guard (Item 3). Add on Item 2/3 landing.
