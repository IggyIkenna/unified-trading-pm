---
type: audit-result
title: Infrastructure Master — CI/CD Pipeline Contract Audit (2026-06-01)
epic: infrastructure_master
auditor: ikenna (slot 1 main, Opus 4.8 1M)
date: 2026-06-01
status: complete
instructions_ref: plans/audit/instructions/infrastructure_master_audit_instructions.md
scope_subset: CI/CD Pipeline Contract (checklist h–l only — VM/GCS items a–g not run this pass)
---

# Infrastructure Master — CI/CD Pipeline Contract Audit (2026-06-01)

First run of the **CI/CD pipeline contract** section added to the `infrastructure_master` audit instruction on
2026-06-01. This pass audits **only checklist groups h–l** (the CI/CD contract); the pre-existing VM/GCS/bucket items
(a–g) were not re-run this session.

## ⚠️ CORRECTION (2026-06-01, same day) — i1–i4 used the wrong mechanism

The branch-protection findings below (i1/i2/i4: "16/23 main, 4 on v1 staging, enforce_admins 6/23") were derived from
**classic** branch protection (`/branches/.../protection`). **That is the wrong lens.** The workspace's canonical QG
gate is **rulesets** (`require-quality-gates`), verified by
`scripts/repo-management/verify_branch_protection_check_names.py` (exit 0 = consistent). Re-audited via the canonical
verifier:

- **Rulesets are internally CONSISTENT** (each repo requires exactly the check its workflow emits — no name drift).
- **9/17 repos require `quality-gates-v2`**: alerting, deployment-service, execution, instruments, market-tick-data,
  strategy, UAC, UTL, PM.
- **8/17 still require v1 `quality-gates`**: batch-live-reconciliation, client-reporting-api, deployment-api,
  deployment-ui, ibkr-gateway-infra, market-data-processing, system-integration-tests, trading-agent-service.
- **Real blocker = pre-existing QG-RED, not config.** A repo shows v1 iff its default-branch workflow is still
  `workspace-qg.yml`; flipping it to v2 requires the repo's v2 QG to be **green** first (else the required check blocks
  ALL its merges). 2026-06-01 CI status: `batch-live`, `client-reporting-api`, `ibkr-gateway-infra`, `deployment-api`,
  `system-integration-tests` **fail v2**; `deployment-ui`, `market-data-processing` **fail v1**. Only repos with a green
  v2 run are safely migratable. **This is the deferred `ci_canonical_v2_migration` Phase-4 reason** — it is per-repo
  CODE remediation, not a branch-protection sweep.
- **Mark drift flagged**: `ci_canonical_v2_migration_2026_05_29.md` marks `batch-live` + `deployment-ui` ✅ "v2 done",
  but live rulesets show both on v1 (the v2 workflow exists but is red / ruleset not re-pinned). Do not treat as done.

The classic-protection table below is retained for history but is **superseded** by the ruleset ground truth above.
Tracking: `cicd_contract_hardening_2026_06_01.md` Phase 1 (re-scoped to rulesets) + `ci_canonical_v2_migration`.

## Transparency — where I sampled vs walked exhaustively

- **Walked exhaustively**: branch protection across **all 23 active repos** (`workspace-manifest.json`
  `repositories[*].status == active`), both `main` and `staging` (i1–i4) — via `gh api .../branches/{br}/protection`.
- **Read directly (not sampled)**: `scripts/quickmerge.sh`, `scripts/quality-gates-base/base-service.sh` (sentinel
  write), `scripts/workflow-templates/workspace-qg.yml.tmpl` trigger surface, `deployment-service/cloudbuild.yaml`,
  `deployment-service/buildspec.aws.yaml`, `deployment-service/scripts/vm/create-code-tarballs.sh`.
- **Cross-referenced (not independently re-run)**: full-workspace SIT status (j2–j3) — taken from
  `full_cicd_sit_target_state_2026_05_24.md` (built `@f881579`, not confirmed on a live trigger this pass); LDR-CI-red
  monitoring (i5) — open `[AGENT] P0` in that same plan.
- **Not run this pass (needs a logged-in slot host)**: `verify-slot-host-symmetry.sh` (h6/l1), live
  `gcloud builds triggers list` (k1/k3), Fleet-tab stale-WIP spot-check (l2). Marked AMBER — re-verify on
  `vm-cross-cutting`.

---

## Checklist results

### Promotion path — quickmerge-only, sentinel-gated, no force-push

| Item | Status   | Evidence                                                                                                                                                                                                   |
| ---- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| h1   | 🟢 GREEN | `quickmerge.sh:819` reads `_SENTINEL=".qg_last_passed_sha"` in the Pass-2 verification block; refuses on mismatch.                                                                                         |
| h2   | 🟢 GREEN | `quality-gates-base/base-service.sh:2411` `git rev-parse HEAD > .qg_last_passed_sha` only on clean full exit; `--skip-*`/`--quick` paths do not reach it (confirmed in `ci-cd-flow.md` § Two-Pass + grep). |
| h3   | 🟢 GREEN | `rg "force" quickmerge.sh` → only 2 hits, both comment keywords (`enforce-files-in-agent-mode`, `enforce-branch-slug-convention`). **No `push --force` / `--force-with-lease` anywhere.**                  |
| h4   | 🟢 GREEN | `quickmerge.sh:1089-1091` PR base = `staging` for human commits + `gh pr merge --auto --squash --delete-branch`; `:1112-1113` base = `main` only for `[skip ci]` automation.                               |
| h5   | 🟢 GREEN | `quickmerge.sh:195` rejects `--dep-branch` under the staging-first model; agents route through staging.                                                                                                    |
| h6   | 🟡 AMBER | Not run — needs a logged-in slot host. Re-run `verify-slot-host-symmetry.sh` on `vm-cross-cutting` + each operator laptop.                                                                                 |

### Branch protection — the QG-green-everywhere precursor (walked all 23 active repos)

| Item | Status   | Evidence                                                                                                                                                                                                                                                                                                                 |
| ---- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| i1   | 🔴 RED   | `main` requires `quality-gates-v2` on **16/23**. **7 missing** (`none`): features-service, fund-administration-service, greeks-service, ml-service, deployment-ui, e2e-testing, agent-orchestrator.                                                                                                                      |
| i2   | 🔴 RED   | `staging` requires `quality-gates-v2` on only **9/23**. **4 still pin retired v1** (`quality-gates`/`workspace-qg`): client-reporting-api, deployment-api, ibkr-gateway-infra, market-data-processing-service. **10 are `none`.** Contradicts the "v1 fully retired" claim in `ci_canonical_v2_migration_2026_05_29.md`. |
| i3   | 🟢 GREEN | `allow_force_pushes.enabled == false` on every repo that has protection (sampled UTS-PM / UAC / deployment-service = false).                                                                                                                                                                                             |
| i4   | 🔴 RED   | `enforce_admins == true` on only **6/23** (alerting-service, execution-service, ml-service, unified-api-contracts, unified-trading-library, unified-trading-pm). On the other 17 the QG gate is **admin-bypassable**.                                                                                                    |
| i5   | 🟡 AMBER | LDR unprotected is by-design, but the Tier-A "LDR-CI-red ping" is still an open `[AGENT] P0` in `full_cicd_sit_target_state_2026_05_24.md` — red can still accumulate silently.                                                                                                                                          |

**Full branch-protection matrix (23 active repos):**

| Repo                              | main req-check | staging req-check | enforce_admins (main)    |
| --------------------------------- | -------------- | ----------------- | ------------------------ |
| alerting-service                  | v2             | v2                | ✅                       |
| batch-live-reconciliation-service | v2             | **none**          | ❌                       |
| client-reporting-api              | v2             | **v1 (stale)**    | ❌                       |
| deployment-api                    | v2             | **v1 (stale)**    | ❌                       |
| deployment-service                | v2             | v2                | ❌                       |
| execution-service                 | v2             | v2                | ✅                       |
| features-service                  | **none**       | **none**          | —                        |
| fund-administration-service       | **none**       | **none**          | —                        |
| greeks-service                    | **none**       | **none**          | —                        |
| ibkr-gateway-infra                | v2             | **v1 (stale)**    | ❌                       |
| instruments-service               | v2             | v2                | ❌                       |
| market-data-processing-service    | v2             | **v1 (stale)**    | ❌                       |
| market-tick-data-service          | v2             | v2                | ❌                       |
| ml-service                        | **none**       | **none**          | ✅ (moot — no req-check) |
| strategy-service                  | v2             | v2                | ❌                       |
| unified-api-contracts             | v2             | v2                | ✅                       |
| unified-trading-library           | v2             | v2                | ✅                       |
| unified-trading-pm                | v2             | v2                | ✅                       |
| unified-trading-api               | v2             | **none**          | ❌                       |
| unified-trading-system-ui         | v2             | **none**          | ❌                       |
| deployment-ui                     | **none**       | **none**          | ❌                       |
| e2e-testing                       | **none**       | **none**          | —                        |
| agent-orchestrator                | **none**       | **none**          | —                        |

### SIT at staging + concurrent-push serialization

| Item | Status   | Evidence                                                                                                                                                                                                                                                                                                 |
| ---- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| j1   | 🟢 GREEN | `workspace-qg.yml.tmpl` triggers = `push:[main,staging]` + `pull_request:[main,staging]` (+ `workflow_dispatch`); LDR excluded by design post-cutover.                                                                                                                                                   |
| j2   | 🟡 AMBER | Full-workspace SIT BUILT (`system-integration-tests@f881579`: `run_cross_repo_invariants.sh` + `full-workspace-sit.yml`, clones manifest topo set, nightly 03:00 UTC) but **not confirmed on a live trigger**; per `full_cicd` it already caught real MTDS data_type drift locally.                      |
| j3   | 🔴 RED   | Promotion is **not gated** on the full-workspace SIT — Tier C (auto LDR→staging promotion + SIT-gate) is unstarted (`[AGENT] P1` open). LDR→staging is still manual per-repo quickmerge → staging can drift.                                                                                             |
| j4   | 🟡 AMBER | quickmerge honors `staging_status.locked` (`quickmerge.sh:591,1047-1055`) but it is **advisory + informational** (`:1047` "do not abort — GitHub auto-merge queue will hold the PR"). No hard cross-slot serialization (no flock/queue). Document as a known gap; file if a tighter guarantee is wanted. |

### `main` triggers builds; branch-triggered + tarball alternatives, tagged

| Item | Status   | Evidence                                                                                                                                                                                                                                                                          |
| ---- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| k1   | 🟢 GREEN | `cloudbuild.yaml` (GCP `asia-northeast1-docker.pkg.dev`) + `buildspec.aws.yaml` (ECR) both build, run `quality-gates.sh --no-fix --quick` inside the image, and push; AWS dispatches `service-deployed`. (Live trigger inventory `gcloud builds triggers list` not run — see k3.) |
| k2   | 🟡 AMBER | **Provenance asymmetry.** `buildspec.aws.yaml:44` tags `$ECR_REPO:$VERSION` + `:latest`. `cloudbuild.yaml` pushes **`:latest`-only** (lines 60/68/78/283) — no `:$VERSION`/`:$SHORT_SHA` immutable tag. GCP rollback/audit loses provenance.                                      |
| k3   | 🟡 AMBER | Branch/manual triggers supported (`cloudbuild.yaml` "Manual trigger" header + `scripts/setup-cloud-build-triggers.sh`), but no first-class "build image off branch X for hotfix" wrapper documented. Confirm + document the branch-build recipe.                                  |
| k4   | 🟢 GREEN | `create-code-tarballs.sh` writes mutable `{repo}-code.tar.gz` **and** SHA-pinned `{repo}-code@{sha}.tar.gz` + `{repo}-code@{sha}.manifest.json` sibling manifest (header lines 26-31) — local code is tagged-as-such.                                                             |
| k5   | 🟢 GREEN | `create-code-tarballs.sh` blocks dirty trees by default; `--allow-dirty-tarball` override is "audit logged; emergency hotfixes only" (lines 12, 124, 134).                                                                                                                        |

### Dirty-tree reconciliation

| Item | Status   | Evidence                                                                                                                                                                                        |
| ---- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| l1   | 🟢 GREEN | `scripts/dev/slot-cron-ff-pull.sh` + `slot-git-status-report.sh` + `slot-master-rebase.sh` + `verify-slot-host-symmetry.sh` all present (referenced by CLAUDE.md slot-host-symmetry HARD RULE). |
| l2   | 🟡 AMBER | Not run — needs live Fleet-tab / git-status report read. Re-verify no slot worktree dirty >1 session.                                                                                           |

**Tally: 9 GREEN · 7 AMBER · 4 RED.**

---

## Gap items (ready to paste into a plan)

The RED/AMBER items below extend the existing CI/CD target-state plan rather than create a new one — they belong with
the Tier A–E work already tracked in `plans/active/issues/full_cicd_sit_target_state_2026_05_24.md`
(`parent_epic: infrastructure_master`).

- [ ] [INFRA] P0. **Branch-protection sweep — `quality-gates-v2` required on `main`+`staging` for ALL 23 active repos.**
      Add the required check to the 7 main-`none` repos (features-service, fund-administration-service, greeks-service,
      ml-service, deployment-ui, e2e-testing, agent-orchestrator) — OR record an explicit `BLOCKED-OPERATOR-DECISION`
      exemption for harness/separate-deploy repos (e2e-testing, agent-orchestrator). Migrate the 4 staging-v1 repos
      (client-reporting-api, deployment-api, ibkr-gateway-infra, market-data-processing-service) to `quality-gates-v2`.
      Add the required check to the 10 staging-`none` repos. (audit i1/i2) — parent_epic: infrastructure_master
- [ ] [INFRA] P1. **Enable `enforce_admins` on `main`+`staging` for the 17 repos where the gate is admin-bypassable**
      (everything except the 6 already-true). Without it, the QG gate is not actually mandatory. (audit i4) —
      parent_epic: infrastructure_master
- [ ] [INFRA] P1. **GCP cloudbuild immutable-tag parity** — push `:$SHORT_SHA` (and/or `:$VERSION`) in addition to
      `:latest` in `deployment-service/cloudbuild.yaml`, matching `buildspec.aws.yaml`, so GCP image rollback/audit has
      provenance. (audit k2) — parent_epic: infrastructure_master
- [ ] [INFRA] P2. **Document the branch-triggered hotfix/dev image-build recipe** (one wrapper or a codex section over
      `setup-cloud-build-triggers.sh` + manual cloudbuild) so an image can be built off an arbitrary branch without
      `main`. (audit k3) — parent_epic: infrastructure_master
- [ ] [INFRA] P2. **Decide concurrent-push serialization guarantee** — confirm whether the advisory
      `staging_status.lock` + GitHub auto-merge queue is sufficient, or add hard cross-slot serialization (flock/queue)
      to quickmerge. Document the decision in `ci-cd-flow.md`. (audit j4) — parent_epic: infrastructure_master
- [ ] [AGENT] P2. **Re-run the live-host CI/CD checks on `vm-cross-cutting`**: `verify-slot-host-symmetry.sh` (h6/l1),
      `gcloud builds triggers list` (k1/k3), full-workspace-sit live trigger (j2), Fleet stale-WIP spot-check (l2). —
      parent_epic: infrastructure_master

**Already-tracked (do NOT duplicate)** — these audit findings map to existing open items in
`full_cicd_sit_target_state_2026_05_24.md`:

- audit i5 → Tier A `[AGENT] P0. LDR-CI-red monitoring/ping`
- audit j2 → Tier B full-workspace SIT (BUILT `@f881579`; confirm live)
- audit j3 → Tier C `[AGENT] P1. auto LDR→staging promotion bot`
- audit k1 (Cloud Run deploy for HTTP-served services) → Tier D `[AGENT] P1. per-service Cloud Run deploy-config audit`

## Active plans created / extended

New named-successor plan created 2026-06-01 to absorb the untracked gaps (this is the "workspace-wide
branch-protection-hygiene sweep" that `workspace_repo_branch_protection_gaps_2026_05_29.md` explicitly deferred):
**[`plans/active/cicd_contract_hardening_2026_06_01.md`](../../active/cicd_contract_hardening_2026_06_01.md)**
(`parent_epic: infrastructure_master`, `assigned_vm: vm-cross-cutting`).

| Gap (audit item)                                       | Absorbed by                                                               | Phase   |
| ------------------------------------------------------ | ------------------------------------------------------------------------- | ------- |
| i1/i2 workspace branch-protection + v1-staging cleanup | `cicd_contract_hardening_2026_06_01.md`                                   | Phase 1 |
| i4 enforce_admins workspace tail                       | `cicd_contract_hardening_2026_06_01.md`                                   | Phase 2 |
| k2/k3 GCP immutable-tag parity + branch-build recipe   | `cicd_contract_hardening_2026_06_01.md`                                   | Phase 3 |
| j4 concurrent-push serialization decision              | `cicd_contract_hardening_2026_06_01.md`                                   | Phase 4 |
| i5 LDR-CI-red monitoring                               | `full_cicd_sit_target_state_2026_05_24.md` Tier A `[AGENT] P0` (existing) | —       |
| j2 full-workspace SIT                                  | `full_cicd_sit_target_state_2026_05_24.md` Tier B (built)                 | —       |
| j3 auto LDR→staging promotion                          | `full_cicd_sit_target_state_2026_05_24.md` Tier C `[AGENT] P1` (existing) | —       |
| k1 Cloud Run deploy for HTTP services                  | `full_cicd_sit_target_state_2026_05_24.md` Tier D `[AGENT] P1` (existing) | —       |

## Archive condition

Archives when all 6 gap items above are `- [x]` in their parent plan(s) AND the next run of checklist h–l is all-GREEN
(or AMBER items have a recorded operator-acked exemption).
