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
- [x] ✅ [SCRIPT] P1. e2e-testing editable self-install — add package-discovery to `pyproject.toml` (QG hygiene).
      (cicd_contract_hardening #1) — e2e-testing@23424ff | changed `[tool.setuptools.packages.find] include = []` → `[tool.setuptools] packages = []`; bypasses flat-layout autodiscovery that caused "Multiple top-level packages" error on `uv pip install -e .`; QG green.
- [x] ✅ [SCRIPT] P2. Wave-1 accommodation cleanup — revert the gate-loosenings now that the fleet is green.
      (cicd_contract_hardening #8) — PM@7adfefec9 (centralize PYSEC-2024-277/2025-183/2026-161 to fleet base) | e2e-testing@33549fe (MAX_DURATION env-override + remove centralized CVEs) | features-service@8e11b2e4 (MAX_DURATION env-override + remove centralized CVE comment block)
- [ ] [SCRIPT] P3. Remove now-redundant local PYSEC-2024-277/2025-183/2026-161 entries from remaining repos:
      alerting-service, client-reporting-api, ml-service, system-integration-tests, trading-agent-service,
      unified-trading-api, unified-trading-library, greeks-service, strategy-service. (cicd_contract_hardening #8 follow-up)

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

- [x] ✅ [SCRIPT] P1. `orphan-ping-audit` 4h local crontab — add a self-pull (Cloud Run copy exempt). (qg_commit L399) — PM@aa65d40a3 | added `K_SERVICE`-guarded `git pull --ff-only` at top of `audit_ping_orphans.sh`; Cloud Run exempt (clones fresh); lifecycle header added.
- [ ] [OPS] P0. AWS-VM half — verify `ROOT_PM`/`SLOT_DIR` + crons + not-stranded (Harsh-laptop half done; must run on
      the VM). (qg_commit L435/L441)
- [ ] [DESIGN] P3. LATER — crons self-pull from a QG-v2-gated ref (successor hardening; the self-pull already removed
      the foot-gun). (qg_commit L452)
- [ ] [CICD] P2. deployment-service CodeBuild BUILD exit 127 (uv/image not found) — live infra red, non-blocking
      (CodeBuild not required). (qg_commit L604)
- [x] ✅ [SCRIPT] P2. Finish the codex-not-a-separate-repo cleanup — `major-bump-approval.yml` write-back +
      `setup-workspace` clone remain. (qg_commit L808) — PM@8676d86 | fixed broken `unified-trading-codex/` runtime paths in `compute-epic-readiness.py` (WORKSPACE_ROOT→PM_ROOT, REPOS_DIR/EPICS_DIR now resolve to `unified-trading-pm/codex/`) and stale default in `check-repo-readiness.py` (`_PM_ROOT / "codex"`).

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

## 2026-06-22 — pytest-cov + xdist coverage-measurement bug (spurious fail-under)

Discovered on market-tick-data-service: QG coverage gate FAILED reporting "total of 46.4% < fail-under=79.0", but the
SAME run's `coverage.xml` (which combines the xdist workers) showed the REAL coverage = **83.95%** (only 1 genuinely
untested file). Root cause: pytest-cov + xdist `-n auto` (2 workers) — the `--cov-report=xml` combines worker data
correctly, but the terminal `--cov-fail-under` enforcement reads PARTIAL (controller-only) data → spurious low number →
false gate failure. ALL repos set `[tool.coverage.run]` with NO `parallel`/`concurrency`, so this is LATENT fleet-wide
(a bad xdist split can spuriously fail any repo's coverage gate). Fix = `parallel = true` +
`concurrency = ["thread","multiprocessing"]` + `sigterm = true` in `[tool.coverage.run]` so the combine is deterministic
+ the fail-under reads combined data.

- [x] ✅ [CICD] P1. **mtds coverage parallel-combine fix SHIPPED** (market-tick-data-service@4a514cf, on LDR) — QG now
      green (coverage reads the real 83.95%, was spuriously failing at 46.4%). Verified: full QG PASSED 78s.
- [ ] [CICD] P1. **Roll the coverage parallel-combine config fleet-wide** — add `parallel`/`concurrency`/`sigterm` to
      every repo's `[tool.coverage.run]` (currently 0/24 set it) so the xdist spurious-fail-under can't strike another
      repo. Best via the canonical pyproject template / propagation. repo: all service repos. Provenance: mtds spurious
      46.4% coverage-gate failure 2026-06-22.

## 2026-06-22 — mtds HTTP-timeout-hardening WIP (preserved, ship-blocked by file-size)

A stale prior-session WIP in the mtds slot (bounded `aiohttp.ClientTimeout(sock_connect=15,sock_read=60,total=120)`
across ~41 DeFi/handler/adapter fetch paths — `backfill_vm_silent_worker_stall_watchdog P3`) was reconciled best-of-both
onto current LDR (1 conflict resolved) + preserved on `origin/wip-preserve/mtds-http-timeouts-2026-06-22`. All 5160
tests pass, but it can't quickmerge-ship: the additive lines push 4 files over 900L (gas_fee_handler 909, polymarket 904,
lending_indices 904, umi_tick_provider 902) + 2 functions over 50L (gas_fee `_collect_solana_live` 52L, `_collect_btc_fees`
54L). The clone is now CLEAN + current (the operator's "dirty + behind LDR" is resolved); the WIP is safe on the branch.

- [ ] [MTDS] P3. **Ship the mtds HTTP-timeout-hardening WIP** — restore from `wip-preserve/mtds-http-timeouts-2026-06-22`,
      extract the per-file `_BACKFILL_HTTP_TIMEOUT` (34 duplicates) into ONE shared module + import it (DRY; drops the 4
      over-900 files back under), trim the 2 over-50L gas_fee_handler functions, QG-green, quickmerge. repo:
      market-tick-data-service. Provenance: stale-WIP reconcile 2026-06-22.
