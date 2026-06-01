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
