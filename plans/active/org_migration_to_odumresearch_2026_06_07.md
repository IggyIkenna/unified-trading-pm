---
title: GitHub Org Migration — IggyIkenna → OdumResearch (fleet-wide, incl. GCP/AWS/deploy)
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
estimate_class: infra
estimate_baseline_ai_days: 10
estimate_calibrated_ai_days: 8
locked_by: live-defi-rollout
locked_since: 2026-06-07
created: 2026-06-07
author: ikennaigboaka [slot-1·laptop]
source:
  - operator-decision-2026-06-07 (do the org migration; org name = OdumResearch; everything moves)
  - read-only pre-audit 2026-06-07 (3 parallel agents: cloud-trust, deploy/VM, github-config)
---

# GitHub Org Migration — `IggyIkenna` → `OdumResearch`

> **Operator decision (2026-06-07):** move ALL repos to a GitHub **Team org `OdumResearch`**. Reason is structural, not
> just to unblock AO branch protection: org-level rulesets (define gates ONCE fleet-wide), org-level secrets (one
> `GH_PAT`/Slack/creds home), team access (Harsh as member), bus-factor (survives one personal account), AND it finally
> unlocks private-repo branch protection on `agent-orchestrator` (today 403 "Upgrade to Team" — rulesets on a private
> **personal** repo are no longer available on Pro).
>
> **Sequencing decision (operator):** get **as much CI/CD hardening done FIRST** (finish `cicd_contract_hardening`
> drain + greening) so we migrate a GREEN, drained pipeline — never migrate a half-jammed fleet. The org cut is its own
> window, AFTER the pipeline is healthy. (Rule-11: do not run two fleet-wide moving things at once.)
>
> **Autonomy contract:** `cursor-configs/AUTONOMOUS_AGENT_RULES.md` (finish-to-done) + `SUB_AGENT_MANDATORY_RULES.md`.
> The owner-rename has a **GitHub auto-redirect safety net** (git SSH/HTTPS clones + most API keep working old→new), so
> the cut is low-risk for git; the genuine must-change surface is the redirect-UNreliable set (WIF trust, Cloud Build /
> CodeStar connections, `gh api repos/.../dispatches`, reusable-workflow template SSOTs, hardcoded-literal guards).

---

## 🔎 PRE-AUDIT MANIFEST (read-only, 2026-06-07) — the full migration surface

Total `IggyIkenna/` footprint: **985 refs across 331 files** (204 `.md` docs, ~100 functional: 34 `.sh`, 32 `.py`, 34
`.yaml/.yml`, 6 `.json`). Classified by **redirect-safety**:

### A. GitHub — MUST-CHANGE (redirect-unreliable or silently-wrong)

- **Central SSOT constant:** `deployment-service/deployment_service/deployment_config.py:376` →
  `github_org: str = Field(default="IggyIkenna")`. The org SSOT; `tests/unit/test_deployment_config.py:115` asserts it.
- **workspace-manifest.json:** 24 × `repositories.<repo>.github_url = https://github.com/IggyIkenna/<repo>` (no
  top-level owner field — string-replace all 24).
- **Reusable-workflow `uses:` refs (hardcoded, NOT `./`):** every repo's `.github/workflows/quality-gates-v2.yml` →
  `uses: IggyIkenna/unified-trading-pm/.github/workflows/python-quality-gates-v2.yml@live-defi-rollout` (+ 2 composite
  actions `setup-python-tools@main`, `setup-agent-tools@main`). Redirect resolves, but the **PM template SSOTs**
  (`scripts/workflow-templates/quality-gates-v2.yml.tmpl`, `scripts/propagation/rollout-quality-gates-ci-workflows.py`)
  MUST be re-rendered or every new rollout re-injects the old owner.
- **Hardcoded-literal owner refs (~108)** — the dangerous subset that SHADOWS `${{ github.repository_owner }}`:
  - **SILENT KILLER:** all 24 repos' `main-backmerge-to-ldr.yml:229` guard
    `if: github.repository == 'IggyIkenna/unified-trading-pm'` → goes **false** post-rename → back-merge silently stops
    firing.
  - PM `GH_ORG: IggyIkenna` / `OWNER="IggyIkenna"` constants: `semver-agent.yml:50`, `staging-to-main.yml:959`,
    `sit-gate.yml:156`, `sit-unlock.yml:146`, `downstream-fix-agent.yml`, `plan-health-agent.yml:144`,
    `rules-alignment-agent.yml`, `overnight-agent-orchestrator.yml`, `rollout-action-ref.yml`,
    `conflict-resolution-agent.yml`, `major-bump-approval.yml`, `agent-audit.yml:46`.
  - Service repos: `execution-service/{plan-alignment-agent,benchmarks}.yml`, `strategy-service/agent-audit.yml`,
    `system-integration-tests/{full-workspace-sit,sit-plan-sync-agent,performance-test,smoke-test-gate}.yml`,
    `features-service`+`fund-administration-service` `{uac-registry-sync,uic-openapi-sync}.yml`
    (`repository: IggyIkenna/unified-api-contracts`).
- **PM scripts hardcoding `IggyIkenna/` (76 refs / ~44 files):** `quickmerge.sh`, `workspace/load-gh-token.sh:93`,
  `repo-management/{pin_branch_protection_rulesets.py, set-branch-protection.sh, apply-branch-protection.sh, create-github-repos-and-collaborators.py, ensure-git-and-origin.py, verify-gh-pat-secrets.sh, verify_branch_protection_check_names.py, admin-force-sync-all-to-main.sh, check-dep-alignment.py}`,
  `propagation/{rollout-agent-workflows.sh, rollout-quality-gates-ci-workflows.py, rollout-ui-build-infra.py, fix-gh-actions-pm-clone.py}` +
  templates, `setup-workspace-from-manifest.sh`, `rollout-manifest-driven-setup.sh`, `verify-slot-host-symmetry.sh`,
  `deploy/trading-kill-switch.sh`, AWS Amplify `*amplify-app-config.json`.

### B. GitHub — RENAME-SAFE (auto-resolve; verify only)

- 196 workflow files derive owner via `${{ github.repository_owner }}` — semver-agent API body, staging-to-main (most),
  ci-status-update, request-major-bump, update-repo-version, major-bump-issue-handler. No edit needed; smoke-verify.
- All git remotes (SSH `git@github.com:IggyIkenna/<repo>.git`) — redirect works, but re-point anyway (Phase B7).

### C. Cloud GCP — MUST-CHANGE (cloud-side; NOT in terraform for WIF)

- **WIF/OIDC trust** (gcloud-applied, documented in `codex/05-infrastructure/auth-setup.md:166`, `gha-wif-migration.md`,
  `agent-orchestrator/docs/OPERATIONS.md:735`): pool
  `--attribute-condition "assertion.repository_owner=='IggyIkenna'"` + per-repo `iam.workloadIdentityUser` binding
  `principalSet://.../attribute.repository/IggyIkenna/<repo>`. Consumers: `agent-orchestrator/deploy-dashboard.yml`,
  `unified-api-contracts/weekly-validation.yml`. **All WIF auth breaks on rename unless re-pointed.**
- **Cloud Build connection:** `terraform/cloud-build/gcp/{variables.tf:18,terraform.tfvars}`
  `github_owner="IggyIkenna"`; GCP 2nd-gen connection named `iggyikenna-github` (`cloud-build/gcp/main.tf:136,161`).
  Flip var + **re-authorize the connection to the OdumResearch org** (OAuth re-link).

### D. Cloud AWS — partial

- **No AWS OIDC provider** — AWS CI uses **static keys** (`AWS_ACCESS_KEY_ID/SECRET`) → unaffected by rename.
- **CodeStar connection** `unified-trading-github` (`cloud-build/aws/main.tf:248`) build
  `location = github.com/${github_owner}/<repo>` + `github_owner` tfvar → flip + **re-authorize CodeStar to
  OdumResearch**.

### E. Deployment / VM — LAUNCH-CRITICAL clones

- `create-code-tarballs.sh` + tarball siblings = **CLEAN** (operate on local worktrees; no owner refs).
- **VM launchers (break a VM at boot):**
  `deployment-service/scripts/vm/{launch-planning-vm.sh:144, launch-epic-vm.sh:238, launch-epic-vm-aws.sh:242, launch-central-brain-aws.sh:147}`,
  `agent-orchestrator/scripts/bootstrap_vm.sh:48,49,310,334-337`,
  `deployment-service/packer/agent-orchestrator/ scripts/warm-cache.sh:41-44` (**4 clones BAKED INTO THE AMI → rebuild
  AMI**), `e2e-testing/scripts/{sports/ vm_setup_and_run.sh, prediction/setup-backfill-vm.sh}`,
  `market-tick-data-service/scripts/ cron_subgraph_health_probe_entrypoint.sh`,
  `unified-trading-pm/scripts/agents/cron_orphan_ping_audit_entrypoint.sh`.
- **Build-time clones + dispatch callbacks (break image builds/deploys):** `setup-cloud-build-triggers.sh:11,57`
  (`GITHUB_OWNER`), ~14 per-repo `cloudbuild.yaml`/`buildspec.aws.yaml` clone dep repos +
  `gh api repos/IggyIkenna/.../dispatches` deploy callbacks (**dispatches may NOT follow redirects → must-change**),
  `deployment-service/templates/{buildspec.aws.yaml,github-actions-aws.yaml}`, `refresh-tarballs.cloudbuild.yaml:124`.

### F. UNAFFECTED (verified — do not touch)

GCP/AWS static SA/access keys · Secret Manager + AWS Secrets Manager secret **names** · Artifact Registry + ECR image
paths (PROJECT_ID/account-derived) · GCS bucket names (`cloud-providers.yaml`, owner-free) · `create-code-tarballs.sh`.

### G. Org-level WINS (consolidate during migration)

- **Secrets:** `GH_PAT` in every repo; `SLACK_WEBHOOK_URL`/`SLACK_CI_WEBHOOK_URL`/`ANTHROPIC_API_KEY`/`GCP_SA_KEY`/
  `TELEGRAM_BOT_TOKEN` recur → set ONCE as **org secrets**, drop per-repo copies.
- **Rulesets:** grandfathered on greeks (`require-quality-gates-main`), mtds (`require-quality-gates` +
  `require-staging-lock-check`), PM (`require-quality-gates`), uac (same two); **AO has NONE (403)**. Re-create at **org
  level** (rulesets are per-repo, NOT inherited on transfer) → AO finally gated.

### H. OPEN BLOCKER (resolve before transfer)

- **`agent-orchestrator` is "Non-transferrable"** in the move UI (cause undetermined — likely environments/deployments,
  a GitHub App install, or attached package). MUST diagnose + clear in AO → Settings before the cut, else AO stays
  personal while the fleet moves (a split worse than either uniform state).

---

## 🧭 PHASED EXECUTION DAG (gates between phases — do not start N+1 until N green)

### PHASE 0 — Pre-migration: finish CI/CD hardening on the CURRENT owner (operator: do this FIRST)

Migrate a GREEN, drained fleet. Gate: the `cicd_contract_hardening_2026_06_01.md` drain is complete.

- [ ] [CICD] P0. Finish the fleet LDR→staging→main drain (deployment-service 31 / greeks 15 / uac 7 behind LDR; 11/18
      promote PRs DIRTY/BLOCKED on uac-0.2.0/utl-0.4.0 dep-bumps). Pipeline self-sustaining BEFORE the cut.
- [ ] [CICD] P0. UTL green on LDR (`utl_full_quality_gates_green` 13 open — T0 base) so downstream promotes.
- [ ] [CICD] P1. Propagate canonical workflow templates to all repos' main+staging (the rule-11b fix) so workflow-file
      checkers pass on PRs-to-main; THEN re-harden `[5.5]`/bash-guard. (Currently `[5.5]` non-fatal transitional.)
- [ ] [CICD] P1. Reclassify the AO branch-pin item: NOT "needs Pro" — it needs the Team-org (this plan). Update
      `agent_orchestrator_e2e_workflow_and_execution_scope_2026_06_02.md` G-item + the codex note.

### PHASE 1 — Org setup + transfer prep (reversible; no ownership change yet)

- [ ] [INFRA] P0. Create GitHub **Team org `OdumResearch`**; add Ikenna (Owner) + Harsh (Member); enable Actions, set
      org Actions policy (allow reusable workflows + the composite actions).
- [ ] [INFRA] P0. Set **org-level secrets** (`GH_PAT`, `SLACK_WEBHOOK_URL`, `SLACK_CI_WEBHOOK_URL`, `ANTHROPIC_API_KEY`,
      `GCP_SA_KEY`, `TELEGRAM_BOT_TOKEN`, `WIF_PROVIDER`, `WIF_SERVICE_ACCOUNT`, `AWS_ACCESS_KEY_ID/SECRET`) scoped to
      all repos. Do NOT yet delete per-repo copies (keep until Phase 3 verify).
- [ ] [INFRA] P0. **Resolve AO "Non-transferrable"** (Blocker H): inspect AO → Settings (environments / installed GitHub
      Apps / packages / deployments); remove/transfer the blocking resource; confirm AO becomes transferrable.
- [ ] [SCRIPT] P0. Build `scripts/migration/org_rename_sweep.py` (idempotent, `--dry-run`/`--apply`,
      `--scope     functional|docs|all`): rewrites `IggyIkenna/` → `OdumResearch/` across the MUST-CHANGE surface (A) —
      manifest 24 urls, `deployment_config.py` github_org + its test, the reusable `uses:` SSOT templates, the ~108
      hardcoded-literal workflow refs incl. the `main-backmerge` guard, the 76 PM-script refs, terraform `github_owner`,
      the VM-launcher + cloudbuild clone URLs + `dispatches`. Dry-run it; record the exact change count per file. DO NOT
      apply yet.
- [ ] [INFRA] P1. **Snapshot for rollback:** export current rulesets (4 repos), per-repo secret name inventory, WIF pool
      attribute-condition + all principalSet bindings, terraform state, Cloud Build/CodeStar connection ids.
- [ ] [INFRA] P1. Coordinate a **cutover window** (no active deploys/promotes mid-flight; pause FF-crons + AutoSpawn;
      announce on every active plan banner `> 🟡 ORG MIGRATION IN PROGRESS`).

### PHASE 2 — THE CUT (transfer + re-point, single window) ⚠️ irreversible-ish (redirects are the net)

- [ ] [INFRA] P0. **Transfer all 24 repos** `IggyIkenna/*` → `OdumResearch/*` (AO last, after Blocker H cleared). GitHub
      auto-creates owner redirects. Verify each lands + redirect active.
- [ ] [INFRA] P0. Re-point **parent-clone `origin` remotes** to OdumResearch on: both operator laptops + EVERY live VM
      (`git remote set-url origin git@github.com:OdumResearch/<repo>.git`). One per repo covers all its slot worktrees
      (worktrees share `.git/config`). `setup-tab-worktrees.sh` uses `origin` symbolically — no edit.
- [ ] [SCRIPT] P0. **Apply `org_rename_sweep.py --apply --scope functional`** on LDR: manifest, deployment_config.py
      (+test), reusable-workflow SSOT templates, the ~108 hardcoded-literal refs (esp. `main-backmerge` guard), 76
      script refs. Commit per logical unit; QG-green; quickmerge. Then `rollout-*` the re-rendered workflow templates +
      composite-action refs to all repos.

### PHASE 3 — Re-wire cloud + deploy (after transfer; redirects buy time)

- [ ] [INFRA] P0. **GCP WIF:** update pool `--attribute-condition` to `repository_owner=='OdumResearch'`; re-create
      every per-repo `iam.workloadIdentityUser` principalSet binding to `attribute.repository/OdumResearch/<repo>`.
      Verify `agent-orchestrator/deploy-dashboard.yml` + `uac/weekly-validation.yml` auth succeeds.
- [ ] [INFRA] P0. **GCP Cloud Build:** flip `terraform/cloud-build/gcp` `github_owner=OdumResearch`; **re-authorize the
      2nd-gen connection** to the OdumResearch org (rename/replace `iggyikenna-github`); `terraform apply`; trigger a
      build to confirm.
- [ ] [INFRA] P0. **AWS CodeStar:** flip `terraform/cloud-build/aws` `github_owner=OdumResearch`; **re-authorize the
      CodeStar connection** `unified-trading-github` to OdumResearch; `terraform apply`; confirm a build location
      resolves. Verify AWS static-key flows (`persist-cicd-event.yml`) still work (unaffected, but smoke).
- [ ] [SCRIPT] P0. **Deploy/VM clone URLs:** apply sweep to the ~10 VM launchers + `bootstrap_vm.sh` +
      `setup-cloud-build-triggers.sh` + ~14 `cloudbuild.yaml`/`buildspec.aws.yaml` (clone URLs + `dispatches`
      callbacks). **Rebuild the AO AMI** (`warm-cache.sh` bakes 4 clones). Roll out per-repo build configs.
- [ ] [INFRA] P1. **Org rulesets:** re-run `pin_branch_protection_rulesets.py` against OdumResearch (or define ONE
      org-level ruleset): `quality-gates-v2` required + `enforce_admins` on `main` (+ `staging` lock) for ALL repos —
      **including agent-orchestrator** (finally gated; closes the AO branch-pin item).
- [ ] [INFRA] P1. **Consolidate secrets:** confirm org secrets resolve in CI; delete redundant per-repo copies.

### PHASE 4 — Verify (the cut is "done")

- [ ] [VERIFY] P0. `rg "IggyIkenna/" --glob '!**/*.md'` across the workspace = **0 functional refs** (docs may lag to
      Phase 5). No `github.repository == 'IggyIkenna/...'` guards remain.
- [ ] [VERIFY] P0. `quality-gates-v2` green on every repo under OdumResearch (trigger v2 per repo); the
      reusable-workflow `uses:` resolves to the new owner; promote cascade (LDR→staging→SIT→main) fires; semver-agent +
      tab-mirror + `main-backmerge` guard all fire under the new owner.
- [ ] [VERIFY] P0. WIF auth works (run deploy-dashboard / weekly-validation); GCP Cloud Build + AWS CodeStar triggers
      fire; **launch one test VM end-to-end** (clones from OdumResearch at boot, comes up healthy) before trusting the
      fleet launchers.
- [ ] [VERIFY] P1. AO ruleset active + `enforce_admins` on; `verify_branch_protection_check_names.py` clean fleet-wide;
      `regenerate_active_plan_inventory.py` clean.

### PHASE 5 — Cleanup + docs + archival

- [ ] [DOCS] P2. Sweep the 204 `.md` + codex (`auth-setup.md`, `gha-wif-migration.md`, AO `OPERATIONS.md`, CLAUDE.md +
      SUB_AGENT/AUTONOMOUS rules version-graduation examples) `IggyIkenna` → `OdumResearch`.
- [ ] [DOCS] P2. Post-phase codex audit: update every SSOT the migration touched; add `MIGRATED` banner where ownership
      assumptions changed. Update this plan's Progress Log + archive (5-step) when all phases green.
- [ ] [INFRA] P3. Keep GitHub redirects as the rollback net for a grace period (≥2 weeks); then optionally retire.

---

## Rollback

The cut's safety net is **GitHub owner redirects** (git clones + most API resolve old→new automatically). If a Phase-2/3
step regresses CI/deploys: redirects keep git working while we fix forward; WIF/Cloud-Build/CodeStar are re-pointable
back to `IggyIkenna` from the Phase-1 snapshot. No repo content is at risk (transfer preserves history/issues/PRs).

## Parallelization

Per-repo ref-sweeps + per-repo build-config rollouts = one sub-agent each (inject `SUB_AGENT_MANDATORY_RULES.md`), max
~10 concurrent, never two on the same repo. Primary owns: the transfer order, WIF/connection re-auth (single-threaded,
credential-sensitive), the cutover sequencing, and verification.

## Success criteria (the migration is "done")

All 24 repos under `OdumResearch`; 0 functional `IggyIkenna/` refs; `quality-gates-v2` green + required fleet-wide incl.
AO; WIF + Cloud Build + CodeStar auth working; a test VM launches+clones clean; secrets consolidated to org; rulesets at
org level; redirects retained as net. Every forced-tradeoff + impossibility recorded in the Progress Log.

## Progress Log (append-only)

- 2026-06-07: Plan authored from a 3-agent read-only pre-audit (cloud-trust / deploy-VM / github-config). Surface mapped
  (985 refs/331 files; must-change vs redirect-safe vs unaffected classified). Awaiting: Phase 0 (finish CICD drain)
  before Phase 1. Open blocker H (AO non-transferrable) to diagnose in Settings.
