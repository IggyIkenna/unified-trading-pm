---
title: CI/CD Quality Gates — quickmerge, quality-gates.sh, local↔CI parity, worktree ship discipline
name: cicd_quality_gates_2026_06_18
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
created: 2026-06-18
status: active
locked_by: live-defi-rollout
locked_since: 2026-06-18
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4
parent_consolidation: cicd_docs_and_consolidation_2026_06_18
source:
  - qg_commit_quality_boundary_and_slot_ff_push_2026_06_03 (consolidated)
  - ci_local_qg_parity_2026_06_08 (consolidated)
  - worktree_ldr_unification_2026_06_08 (consolidated)
  - cicd_contract_hardening_2026_06_01 (quality-gates subset)
---

> **Consolidated 2026-06-18** (see `cicd_docs_and_consolidation_2026_06_18`). **SSOT:**
> `codex/08-workflows/ci-cd-flow.md` (the two-pass model, the QG sentinel, Path-B) + `CICD-WORKFLOW-CATALOG.md`. Zero
> open items dropped.

# CI/CD Quality Gates

**Scope.** The local quality boundary and the path to the integration branch: `quickmerge` two-pass + the
`.qg_last_passed_sha` / content sentinel, local↔CI byte-parity, and the Path-B per-slot worktree ship discipline.

## Open work

### Local ↔ CI parity + QG mechanics

- [ ] [SCRIPT] P1. Fix any non-SIT-delta divergence in the local↔CI matrix to byte-identical (the drive-to-parity
      catch-all; most root-causes closed, the catch-all stays). (ci_local_qg_parity)
- [ ] [SCRIPT] P2. QG dep-clone ref-determinism — resolve all deps at the same ref (no mixed-ref clone).
      (cicd_contract_hardening #23; composes with the LDR→staging drain verify in cicd_promotion_pipeline)
- [ ] [INFRA] P2. Churn-protection: idempotent plan-inventory regen + manifest-canonical-form + a `prettier --check`
      gate (three named writers still churn the worktree). (cicd_contract_hardening #2)
- [ ] [SCRIPT] P1. e2e-testing editable self-install — add package-discovery to `pyproject.toml` (QG hygiene).
      (cicd_contract_hardening #1)
- [ ] [SCRIPT] P2. Wave-1 accommodation cleanup — revert the gate-loosenings now that the fleet is green.
      (cicd_contract_hardening #8)

### Path-B worktree ship discipline (worktree_ldr finish)

- [ ] [DOCS] P2. Rewrite AO `worker.md` + the boot-prompt `branch` fallback off the retired `tab/<op>/N` model.
      (worktree_ldr)
- [ ] [SCRIPT] P3. Prune vestigial tab-branch code in the slot scripts (keep the identity-prefix; careful surgery,
      documented-harmless no-ops). (worktree_ldr)
- [ ] [INFRA] P2. AO drift-tick is staged on LDR, inert until the agent-orchestrator LDR→main promotion lands — activate
      it then. (worktree_ldr)
- [ ] [INFRA] P2. E2e smoke: force a merge-conflict PR → auto-recover + escalate → VM Path-B worker (the closing
      verification; archives the section when green). (worktree_ldr)

### Cron / infra residuals

- [ ] [SCRIPT] P1. `orphan-ping-audit` 4h local crontab — add a self-pull (Cloud Run copy exempt). (qg_commit L399)
- [ ] [OPS] P0. AWS-VM half — verify `ROOT_PM`/`SLOT_DIR` + crons + not-stranded (Harsh-laptop half done; must run on
      the VM). (qg_commit L435/L441)
- [ ] [DESIGN] P3. LATER — crons self-pull from a QG-v2-gated ref (successor hardening; the self-pull already removed
      the foot-gun). (qg_commit L452)
- [ ] [CICD] P2. deployment-service CodeBuild BUILD exit 127 (uv/image not found) — live infra red, non-blocking
      (CodeBuild not required). (qg_commit L604)
- [ ] [SCRIPT] P2. Finish the codex-not-a-separate-repo cleanup — `major-bump-approval.yml` write-back +
      `setup-workspace` clone remain. (qg_commit L808)

### Docs / SSOT hygiene (from the 2026-06-18 `docs/repo-management/` reconciliation)

- [ ] [DOCS] P2. Migrate `docs/repo-management/CI-CD-FLOW.md`'s unique bootstrap/venv/dependency-alignment/mock-infra
      content → `codex/05-infrastructure/workspace-setup.md` (currently an 8-line stub), correcting the stale
      sync-to-main / force-push / three-tier bits to as-built (LDR-trunk); then delete `CI-CD-FLOW.md` (it's bannered
      NOT-the-SSOT in the meantime).
- [ ] [DOCS] P3. Repoint the ~18 residual references off the 4 retired CI/CD docs (`CI-CD-FLOW.md` /
      `docs/ci-cd-ssot.md` / `version-cascade-flow.md` / `sync-to-main-flow.md`) → `codex/08-workflows/ci-cd-flow.md`
      across `.cursor/rules/*.mdc` (cicd-setup, ci-rollout-ownership, dependency-install-protocol,
      dependency-alignment-and-setup-flow, single-repo-vs-workspace-setup, prettier-docs-formatting,
      quality-gates-propagation-risk) + `codex/05-infrastructure/{cicd-setup,README,new-repo-setup}.md` +
      `scripts/{workspace/workspace-bootstrap.sh, repo-management/sync-all-to-main.sh, repo-management/README-ALIGNMENT-AND-SETUP.md}`;
      drop dead `§7`/`§2` anchors. The retired-doc stubs self-redirect, so this is cleanliness, not correctness.

## Verify-and-flip (likely shipped — confirm, then close)

- [ ] [VERIFY] P3. uac `cassette_orphan_checker` intermittent xdist flakiness — the deterministic siblings were
      root-fixed; confirm + close (was a low-confidence "monitor"). (cicd_contract_hardening #19)

## Closed on consolidation (premise superseded — not carried)

- `[~]` Make tab branch names globally unique (precondition for fleet mirror) — CLOSED: SUPERSEDED-BY-PATH-B (tab
  branches + the tab-mirror are retired). (qg_commit L184)
- `[~]` Semantic cross-plan conflict-detector — CLOSED: SUPERSEDED →
  `orchestrator_agent_type_oversight_coverage_2026_06_17` (cross-link already in-body). (qg_commit L796)
- [x] ✅ [SCRIPT] P2. **Fix the STALE `unified-cloud-interface` reference in the QG cloud-SDK check.**
      `scripts/quality-gates-base/base-service.sh:1072` logs _"Direct cloud SDK imports found (route through
      unified-cloud-interface instead)"_ — but `unified-cloud-interface` is NOT a live repo (absorbed into UTL;
      `get_storage_client`/`get_secret_client` now live in `unified_trading_library.cloud_interface`). Update the message
      to name the current package, and review the stale `--glob '!**/unified-cloud-interface/**'` dead-repo exclusions
      (base-service.sh:1462 + STEP 5.12b § "No hardcoded gs:///s3:// outside unified-cloud-interface"). Edit the PM
      base template, then `rollout-quality-gates-unified.py` fleet-wide. Repo: unified-trading-pm. Provenance:
      2026-06-19 operator spotted the stale ref in the deployment-api QG output. — PM@923ee2e3f | QG-green;
      updated 5 messages in base-service.sh (STEP 5.5/5.11/5.12b) + 2 messages in base-library.sh; removed
      dead `!**/unified-cloud-interface/**` glob exclusion; fleet-wide via sourcing (no rollout needed).

## Continuous verification

Local↔CI: a `quality-gates.sh --no-fix` green tree → the staging-PR `quality-gates-v2` is green with zero non-SIT-delta
divergence. Path-B: no slot is stranded behind LDR (the `slot_drift_check.py` invariant holds fleet-wide).
