---
title: CI/CD contract hardening — workspace-wide gate enforcement + build provenance
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
status: active
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
created: 2026-06-01
locked_by: live-defi-rollout
related_plans:
  - plans/active/issues/full_cicd_sit_target_state_2026_05_24.md
  - plans/active/workspace_repo_branch_protection_gaps_2026_05_29.md
  - plans/archive/2026_05/ci_canonical_v2_migration_2026_05_29.md
source:
  - plans/audit/results/infrastructure_master_audit_2026_06_01.md
---

# CI/CD contract hardening — workspace-wide gate enforcement + build provenance

## HANDOFF — next agent (state as of 2026-06-01)

**Goal:** every repo on `quality-gates-v2` (ruleset required-check = `…/quality-gates-v2`), on all branches
(main + staging + live-defi-rollout), all green. 17-repo ruleset set; **8 were not on v2** at start.

**Token (prerequisite — already solved):** `source unified-trading-pm/scripts/workspace/load-gh-token.sh` → exports
`GH_TOKEN` from `.act-secrets` (workspace root) or Secret Manager; it has `Workflows: write`. The default gh keyring
token does NOT (can't edit `.github/workflows`). Verify a host with `verify-slot-host-symmetry.sh`.

**Per-repo status (8 repos):**

| Repo | main ruleset | main v2 run | enforce | remaining |
| ---- | ------------ | ----------- | ------- | --------- |
| trading-agent-service | **v2** ✅ | **green** ✅ | active | staging+LDR roll v2 + re-pin |
| deployment-api | **v2** ✅ | closure-fix in flight (verify) | active | confirm green; staging+LDR |
| system-integration-tests | **v2** ✅ | **RED** (deeper harness issue) | active | diagnose next failure; staging+LDR |
| deployment-ui | v1 | n/a (no v2 wf) | — | roll out v2 + closure dep_repos + diagnose v1; UI repo needs `pw:L2` |
| market-data-processing-service | v1 | n/a (no v2 wf) | — | roll out v2 + closure + diagnose v1 |
| client-reporting-api | v1 | RED **coverage 69<70** | — | write tests (~1% gap) → green → migrate |
| batch-live-reconciliation-service | v1 | RED **coverage 78.2<80** | — | write tests (~2% gap) → green → migrate |
| ibkr-gateway-infra | v1 | RED **MIN_COVERAGE=0 cfg + cov 46<51** | — | fix MIN_COVERAGE cfg + write tests → green → migrate |

**SYSTEMIC ROOT CAUSE (the real bug):** there is **no canonical `quality-gates-v2` workflow template**, so every v2
caller was hand-copied from `alerting-service` → two defects in nearly every repo: (1) wrong job `name:` (emits
`Quality Gates (alerting-service)` → wrong check context), (2) stale/incomplete `dep_repos`. `dep_repos` MUST be the
**full transitive editable-source closure** (uv resolves `editable+../sibling` recursively); the `workspace-manifest.json`
deps list is **incomplete** vs the pyprojects, so compute the closure from pyprojects:
```
BFS over each repo's pyproject `path = "../<repo>"` lines (see deployment-api → 5, SIT → 12).
```

**DURABLE FIX (do this — prevents recurrence):**
- [ ] [SCRIPT] P0. Create `scripts/workflow-templates/quality-gates-v2.yml.tmpl` (canonical): job `name: Quality Gates (__REPO_NAME__)` + `dep_repos: {{TRANSITIVE_CLOSURE}}` rendered from pyproject sources. Wire into `rollout-workflow-templates.sh` (closure computation). Roll out to ALL 17 repos × {main,staging,live-defi-rollout}; remove `workspace-qg.yml`. Then `pin_branch_protection_rulesets.py --apply` (now safe — derives v2 everywhere).
- [ ] [SCRIPT] P1. `verify_branch_protection_check_names.py` reads `--ref live-defi-rollout` by default; after rollout all branches consistent.

**PROVEN per-repo manual procedure (until the template lands):**
1. `source load-gh-token.sh`. 2. Compute closure (BFS over pyproject sources). 3. Relax `require-quality-gates`
ruleset (`gh api -X PUT .../rulesets/<id> -f enforcement=disabled`). 4. `gh api -X PUT` the workflow file: fix
`name:` → `Quality Gates (<repo>)` + set `dep_repos` to the closure. 5. Re-point ONLY that ruleset's
required-check context to `…/quality-gates-v2` (manual PATCH — do NOT use `pin --apply`, it re-pins staging too;
staging has no v2 yet → would block staging). 6. Re-trigger v2; wait green; re-enable enforcement. 7. For
"everything": roll v2 to staging+LDR, then re-pin staging ruleset.

**SAFE-STATE NOTE:** all 3 touched repos (trading-agent, deployment-api, SIT) have enforcement **active** + main
ruleset = v2. deployment-api/SIT main are blocked-on-v2 until their v2 greens (they were already blocked pre-migration
— this is actionable now, not a regression). **Do not leave any ruleset `enforcement=disabled`.**

**Coverage repos** (`client-reporting-api`, `batch-live`, `ibkr`) need **real tests written** (not floor-lowering /
coverage-gaming). `ibkr` also has a `MIN_COVERAGE=0` config bug to fix first.

---

## Overview

Named successor to the **workspace-wide branch-protection sweep** that
[`workspace_repo_branch_protection_gaps_2026_05_29.md`](issues/workspace_repo_branch_protection_gaps_2026_05_29.md)
explicitly deferred ("Auditing OTHER workspace repos beyond the 5 named here — separate workspace-wide
branch-protection-hygiene sweep can ratchet this later"). It also absorbs the `enforce_admins` workspace tail that the
archived `ci_canonical_v2_migration_2026_05_29.md` deferred (it only reached 6/10 repos), plus three build/flow findings
that were not tracked anywhere.

Provenance: the 2026-06-01 CI/CD-contract audit
([`infrastructure_master_audit_2026_06_01.md`](audit/results/infrastructure_master_audit_2026_06_01.md), checklist
groups h–l of the `infrastructure_master` audit instruction). That run walked branch protection across **all 23 active
repos** and found the QG gate is **not** enforced everywhere — the precursor that must be GREEN before the rest of the
CI/CD target state (`full_cicd_sit_target_state_2026_05_24.md` Tiers A–E) is trustworthy.

**Already tracked elsewhere — do NOT duplicate here** (cross-referenced for completeness):

- LDR-CI-red monitoring (audit i5) → `full_cicd_sit_target_state_2026_05_24.md` Tier A `[AGENT] P0`
- full-workspace cross-repo SIT (audit j2) → `full_cicd...` Tier B (built `system-integration-tests@f881579`)
- auto LDR→staging promotion bot (audit j3) → `full_cicd...` Tier C `[AGENT] P1`
- per-service Cloud Run deploy-config (audit k1-deploy) → `full_cicd...` Tier D `[AGENT] P1`
- branch protection for the original 5 repos → `workspace_repo_branch_protection_gaps_2026_05_29.md` (DONE)

## Why it matters

"QG passes everywhere" is the load-bearing precursor for the whole promotion contract (quickmerge → staging → main →
build). Today the server-side gate is enforced on only 16/23 repos on `main` and 9/23 on `staging`, with 4 repos still
pinning the **retired v1** check and `enforce_admins` true on only 6/23 — so on most repos an admin can merge straight
past a red gate. That is the same class of hole that let `staging` drift ~1 month undetected.

## Phased execution

> **🔑 PREREQUISITE (discovered 2026-06-01 — RESOLVED via provisioning, not a missing credential).** The migrations
> edit `.github/workflows/*.yml`, which the gh **keyring login token (`gho_…`) cannot do** (no `workflow` scope). But
> the existing **`GH_PAT` in Secret Manager IS workflow-capable** (fine-grained, "Workflows: read/write" — verified by a
> non-mutating PUT returning 409, not 403). Fix = make `GH_PAT` the active `GH_TOKEN` in every context via
> `source unified-trading-pm/scripts/workspace/load-gh-token.sh` (now sourced by `workspace-bootstrap.sh`; checked by
> `verify-slot-host-symmetry.sh`; codified in CLAUDE.md § "Workflow-capable GH_TOKEN everywhere"). Also note: git push
> **over SSH** is already exempt from the restriction, so ssh-protocol slots can push workflow files via `git` today.

- [x] ✅ [SCRIPT] P0. **Workflow-capable GH_TOKEN provisioning** — created `scripts/workspace/load-gh-token.sh` (SSOT),
      wired into `workspace-bootstrap.sh`, added a workflow-capability probe to `verify-slot-host-symmetry.sh`, codified
      the HARD RULE in CLAUDE.md. (PM-side, 2026-06-01.)
- [ ] [SCRIPT] P0. **Export GH_TOKEN into orchestrator VM worker envs** — `agent-orchestrator/scripts/bootstrap_vm.sh`
      currently fetches `GH_PAT` only for clone-time HTTPS; also export it as `GH_TOKEN`/`GITHUB_TOKEN` in the worker
      systemd env (or source `load-gh-token.sh` at worker start) so VM workers can edit workflows too. — repo:
      agent-orchestrator
- [x] ✅ [SCRIPT] P1. **trading-agent-service MAIN — MIGRATED 2026-06-01** (first real v1→v2 migration, via the
      workflow-capable `GH_PAT` from `.act-secrets`). Fixed the job-name bug (`Quality Gates (alerting-service)` →
      `(trading-agent-service)`, commit `a8895d19a` to main); main's ruleset was requiring v1 `quality-gates` which no
      longer ran on main (main PRs were fully **BLOCKED**) — relaxed `require-quality-gates` enforcement, landed the fix,
      re-pointed the ruleset to `Quality Gates (trading-agent-service) / quality-gates-v2`, re-enabled enforcement.
      `verify_branch_protection_check_names.py` confirms main=v2 + CONSISTENT. main is now unblocked + on v2.
- [ ] [SCRIPT] P1. **trading-agent-service STAGING + LDR — finish the migration.** STAGING ruleset still requires v1
      and staging has NO `quality-gates-v2.yml` (left intentionally — re-pinning would block staging). LDR still has
      `workspace-qg.yml`. Roll out `quality-gates-v2.yml` to staging + LDR (remove `workspace-qg.yml`), confirm green,
      then `pin_branch_protection_rulesets.py --apply --repo trading-agent-service` (now safe — derives v2 for both).

### Phase 1 — Workspace-wide branch-protection + required-check enforcement (audit i1/i2)

**CORRECTED 2026-06-01: canonical mechanism = RULESETS** (`require-quality-gates`), verified by
`scripts/repo-management/verify_branch_protection_check_names.py` + applied by `pin_branch_protection_rulesets.py`. The
required context is DERIVED from each repo's workflow file, so a repo is "v2" iff its default-branch workflow is
`quality-gates-v2.yml`. Ground truth: **9/17 on v2; 8 still on v1**
(`batch-live-reconciliation`, `client-reporting-api`, `deployment-api`, `deployment-ui`, `ibkr-gateway-infra`,
`market-data-processing`, `system-integration-tests`, `trading-agent-service`).

**This is the deferred `ci_canonical_v2_migration` Phase-4 work, BLOCKED on per-repo QG-RED — NOT a config sweep.**
2026-06-01 CI: `batch-live`, `client-reporting-api`, `ibkr-gateway-infra`, `deployment-api`, `system-integration-tests`
fail v2; `deployment-ui`, `market-data-processing` fail v1. Enabling the v2 required check on a red repo blocks ALL its
merges, so each is gated on its v2 QG going green first (real code/test/lint/codex remediation per repo).

- [ ] [BLOCKED-QG-RED] P0. Per-repo: fix the v2 QG to green, then migrate workflow `workspace-qg.yml → quality-gates-v2.yml`
      on the default branch + re-pin ruleset (`pin_branch_protection_rulesets.py --apply --repo <r>`). Order by readiness:
      first any repo whose v2 run is already green (re-pin only), then the QG-red repos after their QG is fixed. **Do NOT
      flip the ruleset on a red repo.** Owns: the 8 v1 repos above. Tracked jointly with `ci_canonical_v2_migration`.

  **Per-repo fan-out todos (fresh `quality-gates-v2` diagnoses, 2026-06-01 — each dispatchable to a slot):**
  - [ ] [SCRIPT] P1. **deployment-api** — v2 dep-install fails: `Failed to generate package metadata for
        deployment-service==0.1.1 @ editable+../deployment-service`. CI doesn't clone the editable sibling. Fix:
        add `deployment-service` to deployment-api's `dependencies` in `workspace-manifest.json` (so v2 `dep_repos`
        clones it) OR pin the dep to a published tag instead of `editable+../`. Then re-run v2 → green → re-pin ruleset.
  - [ ] [SCRIPT] P1. **system-integration-tests** — v2 dep-install fails: `…metadata for alerting-service==0.1.0 @
        editable+../alerting-service` (same editable-sibling-not-cloned class as deployment-api). Same fix via manifest
        `dep_repos` / tag-pin. Then re-run → green → re-pin.
  - [ ] [TEST] P1. **client-reporting-api** — coverage 69.0% < floor 70.0% (≈1% short). Add tests to clear the floor;
        re-run v2 → green → re-pin ruleset.
  - [ ] [TEST] P1. **batch-live-reconciliation-service** — coverage 78.2% < floor 80.0% (≈2% short). Add tests; re-run
        → green → re-pin. (NB: ci_canonical marks this ✅ but it's live-v1 + red — see reality-check banner there.)
  - [ ] [TEST] P2. **ibkr-gateway-infra** — (a) config bug: `MIN_COVERAGE=0 < system floor 70` in its quality-gates.sh —
        raise `MIN_COVERAGE` to ≥70; (b) actual coverage 46% < 51% — substantial test-writing. Larger effort; fix config
        first, then tests; re-run → green → re-pin.
  - [ ] [SCRIPT] P2. **deployment-ui** — still on v1 (`workspace-qg`), red. Diagnose its v1 failure, roll out
        `quality-gates-v2.yml`, get green, re-pin ruleset. (UI repo — also needs `pw:L2` per the playwright gate.)
  - [ ] [SCRIPT] P2. **market-data-processing-service** — still on v1, red. Diagnose v1 failure, roll out v2, green,
        re-pin.
- [ ] [VERIFY] P0. Re-run `verify_branch_protection_check_names.py` → every repo's required context is `…/quality-gates-v2`;
      0 on v1. Mark each repo's todo done ONLY when its verifier line is live-v2.
- [ ] [OPERATOR-DECISION] P1. Repos NOT in the 17-repo ruleset set (`fund-administration-service`, `greeks-service`,
      `ml-service`, `unified-trading-api`, `unified-trading-system-ui`, `e2e-testing`, `agent-orchestrator`) — confirm
      whether each needs the `require-quality-gates` ruleset added or is legitimately EXEMPT (harness / separate deploy
      path). Record in `feature-branch-workflow.md`.

**Do not duplicate**: the v1→v2 migration itself is owned by `ci_canonical_v2_migration_2026_05_29.md` (which has
mark-drift — `batch-live` + `deployment-ui` marked ✅ but live-v1). This plan only adds the ruleset-mechanism framing +
the not-in-ruleset-set decision; the migration todos live there.

### Phase 2 — enforce_admins workspace tail (audit i4)

Baseline (2026-06-01): `enforce_admins` true on only 6/23 (alerting, execution, ml-service, UAC, UTL, PM).

- [ ] [SCRIPT] P1. Enable `enforce_admins` on `main`+`staging` for every protected repo where it is currently false —
      but ONLY after that repo's `quality-gates-v2` is green (enabling it on a red repo blocks all merges). This is the
      workspace tail of the `ci_canonical` Phase 5 enforce_admins work (which reached 6/10 and deferred the rest).
- [ ] [VERIFY] P1. Confirm `enforce_admins.enabled == true` on all protected repos; document any repo intentionally left
      false (with reason) in `feature-branch-workflow.md`.

### Phase 3 — Image-build provenance + branch-triggered builds (audit k2/k3)

- [ ] [SCRIPT] P1. **GCP immutable-tag parity** — `deployment-service/cloudbuild.yaml` currently pushes `:latest`-only;
      AWS `buildspec.aws.yaml` already tags `:$VERSION`+`:latest`. Add `:$SHORT_SHA` (and/or `:$VERSION`) to the GCP
      `images:` block so GCP rollback/audit has provenance. Verify a build produces the immutable tag in Artifact
      Registry.
- [ ] [DOC] P2. **Branch-triggered build recipe** — document (codex section over `setup-cloud-build-triggers.sh` +
      manual `cloudbuild.yaml`) how to build+push an image off an arbitrary branch for a hotfix / fast-dev cycle without
      promoting through `main`. Note the tarball path (`create-code-tarballs.sh`, SHA-pinned) as the local-code
      alternative.

### Phase 4 — Concurrent-push serialization decision (audit j4)

- [ ] [OPERATOR-DECISION] P2. Decide whether the current advisory `staging_status.locked` flag + GitHub's native
      auto-merge queue is a sufficient concurrent-push guarantee, OR whether quickmerge needs hard cross-slot
      serialization (flock / queue). Today there is no hard serialization beyond the advisory lock. Record the decision
      in `codex/08-workflows/ci-cd-flow.md`; if "add hard serialization", spawn a follow-up implementation todo.

### Phase 5 — PM main↔LDR back-merge drift (discovered 2026-06-01 attempting the LDR→main catch-up) **P0**

Root cause discovered while attempting to promote PM `main` (which was 666 commits behind `live-defi-rollout`): the
PM **doc-fast-path lands commits directly on `main`** (e.g. `a104761b6` "HARD RULE sweep…", `1632fee75` "playwright UI
gate + standards…") but **nothing back-merges those main-only commits into LDR**. Result: `main` and LDR diverge
*both ways*, and the catch-up PR (`#103 live-defi-rollout→main`) is `CONFLICTING/DIRTY` with **~95 conflicting files**
across foreign codex docs / plans / scripts — too large + foreign-saturated to hand-resolve on a slot. This is the
mechanism behind the exact drift this whole audit is about.

- [ ] [SCRIPT] P0. **Auto back-merge `main`→LDR after every direct-to-main PM commit.** Add a GHA on PM (trigger:
      `push: [main]`) that opens/auto-merges a `main → live-defi-rollout` FF/merge PR, so a doc-fast-path commit can
      never strand on main. Mirrors the existing `tab-mirror-to-ldr.yml` direction, in reverse.
- [ ] [OPERATOR-DECISION] P0. **Resolve the current `#103` catch-up.** ~95-file foreign-conflict merge of 670 commits
      into shared `main` — needs operator-coordinated reconciliation (or the doc owners), NOT an autonomous slot merge.
      Options: (a) back-merge `main`→LDR resolving the ~95 conflicts on the integration branch, then `#103` becomes a
      clean FF; (b) reset main to LDR via `run-version-alignment.sh` + a controlled sync (NB: `admin-force-sync-all-to-main.sh`
      can revert semver bumps — human-only). Surface to operator; do not auto-merge.
- [ ] [DOC] P1. Document in `ci-cd-flow.md`: "PM doc-fast-path to `main` REQUIRES a back-merge to LDR (automated by the
      Phase-5 GHA); never leave a main-only commit unmirrored."

## Success criteria

| Phase   | Gate                                                                                                                |
| ------- | ------------------------------------------------------------------------------------------------------------------- |
| Phase 1 | Audit i1/i2 re-run all-GREEN: `quality-gates-v2` on `main`+`staging` for every active non-exempt repo; 0 v1; 0 none |
| Phase 2 | Audit i4 re-run: `enforce_admins` true on every protected repo (or documented exemption)                            |
| Phase 3 | GCP cloudbuild pushes an immutable tag; branch-build recipe documented in codex                                     |
| Phase 4 | Concurrent-push guarantee decided + recorded in `ci-cd-flow.md`                                                     |
| Phase 5 | `main`→LDR back-merge automated; `#103` catch-up resolved by operator; no main-only unmirrored commits              |

## Codex SSOTs

- `codex/06-coding-standards/feature-branch-workflow.md` (per-repo required-check + enforce_admins matrix)
- `codex/08-workflows/ci-cd-flow.md` (branch model + concurrent-push protocol)
- `codex/05-infrastructure/deployment-and-qg-strategy.md` (tarball-vs-image + build provenance)

## Out of scope (named successors)

- v1 workflow **FILE** removal (distinct from the required-CHECK migration in Phase 1) — held for
  `cleanup_v1_quality_gates_workflows_<date>.md` once GH Support ticket #4422570 clears (per archived ci_canonical).
- The active/archive **duplicate** of `ci_canonical_v2_migration_2026_05_29.md` (present in both `plans/active/` and
  `plans/archive/2026_05/`) is a plan-hygiene artifact, not CI/CD machinery — leave for the plan-hygiene sweep.
