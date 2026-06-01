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

Baseline (2026-06-01): `main` v2 on 16/23; `staging` v2 on 9/23; 4 repos on stale v1; 10 staging-`none`.

- [ ] [SCRIPT] P0. Add `quality-gates-v2` as required status check on `main` for the 6 unprotected service repos:
      `fund-administration-service`, `greeks-service`, `ml-service`, `deployment-ui`. Bootstrap the v2 workflow onto the
      target branch first (same admin-merge recipe as UAC/UTL), gated on that repo's QG being green.
- [ ] [OPERATOR-DECISION] P1. `e2e-testing` + `agent-orchestrator` have no `main` required check — confirm whether these
      are legitimately EXEMPT (test harness / separate Firebase+Packer deploy path) or need the gate. Record the
      decision (exempt → `feature-branch-workflow.md` matrix; gate → add to Phase 1).
- [ ] [SCRIPT] P0. Migrate the 4 repos still pinning the **retired v1** check on `staging` to `quality-gates-v2`:
      `client-reporting-api`, `deployment-api`, `ibkr-gateway-infra`, `market-data-processing-service`. Order: drop v1 →
      wait for v2 green → add v2 (minimize the no-check window; same agent turn).
- [ ] [SCRIPT] P1. Add `quality-gates-v2` required on `staging` for the staging-`none` repos that have a `main` gate:
      `batch-live-reconciliation-service`, `unified-trading-api`, `unified-trading-system-ui` (+ any others surfaced).
- [ ] [VERIFY] P1. Re-run the audit i1/i2 sweep — `gh api repos/IggyIkenna/<repo>/branches/{main,staging}/protection`
      across all active repos → every active non-exempt repo has `quality-gates-v2` on both branches; 0 on v1; 0 `none`.

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

## Success criteria

| Phase   | Gate                                                                                                                |
| ------- | ------------------------------------------------------------------------------------------------------------------- |
| Phase 1 | Audit i1/i2 re-run all-GREEN: `quality-gates-v2` on `main`+`staging` for every active non-exempt repo; 0 v1; 0 none |
| Phase 2 | Audit i4 re-run: `enforce_admins` true on every protected repo (or documented exemption)                            |
| Phase 3 | GCP cloudbuild pushes an immutable tag; branch-build recipe documented in codex                                     |
| Phase 4 | Concurrent-push guarantee decided + recorded in `ci-cd-flow.md`                                                     |

## Codex SSOTs

- `codex/06-coding-standards/feature-branch-workflow.md` (per-repo required-check + enforce_admins matrix)
- `codex/08-workflows/ci-cd-flow.md` (branch model + concurrent-push protocol)
- `codex/05-infrastructure/deployment-and-qg-strategy.md` (tarball-vs-image + build provenance)

## Out of scope (named successors)

- v1 workflow **FILE** removal (distinct from the required-CHECK migration in Phase 1) — held for
  `cleanup_v1_quality_gates_workflows_<date>.md` once GH Support ticket #4422570 clears (per archived ci_canonical).
- The active/archive **duplicate** of `ci_canonical_v2_migration_2026_05_29.md` (present in both `plans/active/` and
  `plans/archive/2026_05/`) is a plan-hygiene artifact, not CI/CD machinery — leave for the plan-hygiene sweep.
