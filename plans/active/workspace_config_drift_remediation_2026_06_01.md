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
execution_scope: local-only
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
- [x] ✅ [SCRIPT] P2. **Item 3 — regression guard.** Add a check (PM `quality-gates.sh` step and/or pytest) asserting
      the canonical `.code-workspace` `folders[]` (minus workspace-root) == active+scaffolded repo set in
      `workspace-manifest.json`, and that no listed path is a known archived/consolidated repo. Optionally assert
      `git.scanRepositories`/`git.ignoredRepositories` entries resolve to real repo names. Closes Finding 3 (no guard ⇒
      both drifts went silent). **Script → PR targets `staging`** (bundle with Item 2; include the Item-1 canonical fix
      on the staging branch so the guard is green there too). — unified-trading-pm@79263233d |
      `scripts/quality_gates/check_workspace_code_workspace_drift.py` (basedpyright-clean, strict) wired into
      `quality-gates.sh` post-gates (blocking) + 9-case pytest
      `tests/unit/test_check_workspace_code_workspace_drift.py`. Verified clean on current workspace (25 repos),
      negative tests exit 1. Same LDR-not-staging deviation as Item 2.
- [x] ✅ [PM] P2. **Item 4 — adjudicate the features-service `ci_status` edit (Observation A).** Slot-5 `stash@{0}`
      (`slot5-FOREIGN: features-service ci_status LOCAL_PASS->FAILING`) held an uncommitted flip that was starving
      slot-5 PM's FF-pull cron (963 behind). **Resolved 2026-06-01 (operator-acked: drop stash):** investigated the CI
      first — the authoritative workflow `quality-gates-v2` is **GREEN** on features-service's current LDR HEAD
      (`dd5812b5fb`); the earlier red `quality-gates-v2` runs were fixed by the latest
      `fix(tests): drop project_id     substitution assertions` commit. The failures flooding `gh run list` are all
      `agent-audit.yml` — infra noise (0s duration, "log not found" = the workflow never starts; trigger/permission
      config), not test/quality failures. So committed `ci_status: LOCAL_PASS` is currently accurate and the slot-5
      `FAILING` flip was stale (reflected the pre-fix red state). Dropped `stash@{0}` from slot-5's PM worktree
      (recoverable commit `f98114f266` until GC); the two surviving `stash@{0..1}` are slot-1 WIP, untouched. Slot-5 PM
      tree now clean + 0 behind origin/LDR — FF-pull unblocked.
- [x] ✅ [SCRIPT] P3. **Item 5 — FF-pull starvation watchdog signal (spec delivered).** Spec below (§ "Item 5 spec").
      Proposes the detection rule + ping payload for the slot-5-963-behind failure mode.
- [x] ✅ [SCRIPT] P3. **Item 5b — implement the FF-pull starvation watchdog.** Wired the § "Item 5 spec" `collision`
      detection (incoming-changed-files ∩ dirty-files ≠ ∅, gated on `behind ≥ FF_STARVE_COMMIT_THRESHOLD` or age >
      `FF_STARVE_AGE_HOURS`) into `scripts/dev/slot-git-status-report.sh` (it already walks each repo's ahead/behind +
      dirty state) which POSTs a one-per-(slot,repo) `FF-PULL STARVATION` ping to `/api/slots/<N>/message`
      (`from_role:     main`) the same way it POSTs git-status, de-duped via `.tabs/.ff-starve-state/` markers that
      clear on next successful FF. `slot-cron-ff-pull.sh` stays the actor; the report cron is the detector/alerter.
      Detection logic is a standalone testable `scripts/dev/ff-starvation-detect.sh`. Added
      `tests/test_ff_starvation_detect.bats` (10 cases: collision→signal, non-colliding-dirty→no-signal,
      below-threshold→no-signal, clean/up-to-date→no-signal + syntax + arg-validation). Updated
      `codex/05-infrastructure/per-tab-worktrees.md` § "Step 7" (troubleshooting row + dedicated watchdog subsection).
      **Landed on LDR** (same staging-632-behind deviation as Items 2/3). — code unified-trading-pm@899e36e92 | bats
      10/10 green | full PM QG `--no-fix` exit 0 (basedpyright ratchet held; new scripts are bash, no JSON-parsing
      python so no empty-fallback exclude needed).

## Discoveries (captured per HARD RULE)

- [x] ✅ [SCRIPT] P3. **`agent-audit.yml` fails at 0s with no logs on features-service LDR** (surfaced during Item 4
      investigation). **Root-caused + fixed.** The 0s "log not found" failures are GitHub **`startup_failure`** runs
      ("This run likely failed because of a workflow file issue") — the workflow never starts a job, so there are no
      logs. **Cause**: features-service ran the _legacy inline-prototype_ `agent-audit.yml` whose "Self-dispatch retry
      on failure" step had `if: failure() && fromJSON(inputs.attempt || '1') < 3` plus
      `inputs.attempt`/`inputs.prior_context` in step `env:`. GitHub evaluates those expressions when **compiling the
      workflow for a push event**, where the `inputs` context does not exist → compile error → a `startup_failure` run
      attributed to the push, even though the trigger is `workflow_dispatch`-only. That's why a dispatch-only workflow
      showed "Triggered via push" at 0s on every LDR push. **Scope = NOT workspace-wide**: legacy repos WITHOUT that
      self-dispatch step (e.g. strategy-service, deployment-service) create zero runs; only repos with the
      `fromJSON(inputs.attempt` step startup-fail. The 3 affected repos: **features-service,
      market-data-processing-service, market-tick-data-service**. **Fix applied to features-service**: migrated its
      `agent-audit.yml` to the canonical thin form (reusable `python-quality-gates-v2` call, no `inputs.*` in
      expressions) matching execution-service/instruments-service/UAC; `dep_repos` matches its own
      `quality-gates-v2.yml`. `agent-audit.yml` is NOT a PM-templated workflow, so per-repo edit is correct.
      **Verified**: pushing the fix (features-service@dba0f5bf) created **zero** agent-audit runs (vs a startup_failure
      on every prior push) → compiles clean + correctly dispatch-only. — features-service@dba0f5bf | provenance: Item 4
      investigation 2026-06-01. **Cross-repo follow-ups tracked below.**
- [x] ✅ [SCRIPT] P3. **Migrate `market-data-processing-service` `agent-audit.yml` to the canonical thin form** (same
      `startup_failure`-on-push defect as features-service — had the `fromJSON(inputs.attempt` self-dispatch step).
      Replaced `.github/workflows/agent-audit.yml` with the reusable `python-quality-gates-v2.yml@main` thin form;
      `dep_repos: "unified-trading-library market-tick-data-service unified-api-contracts"` (matches its own
      `quality-gates-v2.yml`). **Verified**: push of the fix created zero new agent-audit runs (latest run predates it).
      — market-data-processing-service@e992a71 | provenance: agent-audit.yml discovery 2026-06-01.
- [x] ✅ [SCRIPT] P3. **Migrate `market-tick-data-service` `agent-audit.yml` to the canonical thin form** (same
      `startup_failure`-on-push defect — confirmed 0s push failures + had the `fromJSON(inputs.attempt` self-dispatch
      step). Replaced `.github/workflows/agent-audit.yml` with the reusable `python-quality-gates-v2.yml@main` thin
      form; `dep_repos: "unified-trading-library unified-api-contracts"` (matches its own `quality-gates-v2.yml`).
      **Verified**: push of the fix created zero new agent-audit runs (latest run predates it). —
      market-tick-data-service@6fcca80f | provenance: agent-audit.yml discovery 2026-06-01.
- [x] ✅ [SCRIPT] P2. **Runbook Execution-Owner check fails on a vendored codex mirror** (surfaced running the Item 5b
      merge-prerequisite QG). `scripts/quality_gates/check_runbook_execution_owner.py` walks the whole workspace for
      `*runbook*.md` and flagged `unified-trading-system-ui/context/codex/05-infrastructure/sit-runbook.md` (no
      frontmatter) — a **stale read-only mirror** of the compliant canonical
      `unified-trading-pm/codex/05-infrastructure/sit-runbook.md`. The baseline was written to 0 in a workspace WITHOUT
      the UI repo checked out, so every full-workspace slot's PM QG was blocked (foreign, pre-existing, not caused by
      this plan's work). **Fixed**: added `context/codex/` to the checker's `EXCLUDED_DIRS` (vendored codex mirrors in
      non-PM repos are never the canonical runbook; the PM `codex/` SSOT stays enforced). Re-verified 0 violations
      scanning 10 runbooks; full PM QG `--no-fix` exit 0. — unified-trading-pm@0f36b7142 | provenance: Item 5b QG run
      2026-06-01.

## Item 5 spec — FF-pull starvation watchdog signal

**Failure mode** (Observation A): slot-5 `unified-trading-pm` sat **963 commits behind** `origin/live-defi-rollout` with
the remote configured correctly. The FF-pull cron (`slot-cron-ff-pull.sh`) silently no-op'd every run because an
**uncommitted foreign edit** to `workspace-manifest.json` collided with incoming commits, so every `git pull --ff-only`
aborted. Nothing alerted — the slot just fell further behind indefinitely. The two existing crons
(`slot-cron-ff-pull.sh`, `slot-git-status-report.sh`) both treat "couldn't FF" as a benign skip.

**Detection rule** (per slot × per repo, evaluated each cron tick):

```
behind   = git rev-list --count HEAD..origin/<integration-branch>
ff_clean = (behind > 0) AND (merge-base HEAD origin/<branch> == HEAD)   # a true fast-forward is possible
dirty    = git status --porcelain=v1 is non-empty
collision = ff_clean AND dirty AND (incoming changed-file set ∩ dirty file set ≠ ∅)
STARVED  = collision AND behind >= THRESHOLD          # THRESHOLD default 25 commits OR age > 6h since last successful FF
```

`collision` (not merely `dirty`) is the precise trigger: a dirty file that does **not** intersect the incoming change
set does not block `--ff-only`, so it is not a starvation cause and must not page. The `behind >= THRESHOLD` / age-gate
avoids paging on normal in-flight work (a slot 1–2 commits behind mid-edit is healthy).

**Signal** — emit ONE orchestrator ping per (slot, repo) while STARVED (de-duplicated; clears on next successful FF):

```
FF-PULL STARVATION — slot <N> / <repo>
behind: <count> commits | last successful FF: <ts or 'unknown'>
blocking dirty files (collide with incoming): <path[, path...]>
owner hint: untracked/unowned? → likely foreign WIP — stash-by-name + FF, do NOT discard
remediation: git stash push -- <colliding paths> && git pull --ff-only && (commit-or-restore the stash)
```

**Wiring** (optional follow-up): add the `collision` computation to `slot-git-status-report.sh` (it already walks each
repo's ahead/behind + dirty state for the dashboard) and POST the signal to the orchestrator backend the same way the
drift reporter posts git-status. `slot-cron-ff-pull.sh` stays the actor (it does the FF); the report cron is the
detector/alerter. Threshold + age-gate live in env (`FF_STARVE_COMMIT_THRESHOLD`, `FF_STARVE_AGE_HOURS`).

**Composes with**: the slot-host-symmetry HARD RULE (every host's slots FF-pull every 5 min) — this watchdog is the "why
didn't it?" alarm for when that contract silently fails. Does NOT auto-resolve the collision (that needs the
stash-by-name + adjudicate judgment from the two-teammates HARD RULE — see Item 4 for an instance).

## Codex SSOT updates

- [x] `codex/05-infrastructure/per-tab-worktrees.md` — documented the canonical-vs-slot `.code-workspace` path-style
      contract (Item 2) + the regression guard (Item 3) in a new "### `.code-workspace` path-style contract" subsection.
      Landed alongside Item 3.
