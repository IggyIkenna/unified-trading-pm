# Unified Trading PM — SSOT Index

Canonical references for plans, manifest, and deployment. See also `unified-trading-codex/00-SSOT-INDEX.md` for Codex
docs.

## Canonical Plans

| Doc                         | Location                                                 | Notes                                                   |
| --------------------------- | -------------------------------------------------------- | ------------------------------------------------------- |
| Plans → Deployable workflow | `plans/active/plans_to_deployable_unified_audit.plan.md` | Four-stage pipeline: Plans → Code → Tested → Deployable |
| Active plans index          | `plans/active/INDEX.md`                                  | Status, blockers, order chain                           |
| Archive                     | `plans/archive/`                                         | Superseded plans only; see README.md                    |

## Manifest and Topology

| Doc                              | Location                                                                                       |
| -------------------------------- | ---------------------------------------------------------------------------------------------- |
| Workspace manifest               | `workspace-manifest.json`                                                                      |
| Topology DAG                     | `WORKSPACE_MANIFEST_DAG.svg`                                                                   |
| Runtime topology                 | `../deployment-service/configs/runtime-topology.yaml`                                          |
| Repo readiness checklists (SSOT) | `../unified-trading-codex/10-audit/repos/{repo}.yaml` (codex v3.0 — CR1-CR5, DR1-DR6, BR1-BR8) |
| Readiness schema template        | `../unified-trading-codex/10-audit/REPO_READINESS_CHECKLIST.yaml`                              |

## Audit and Gates

| Doc                      | Location                                     |
| ------------------------ | -------------------------------------------- |
| Audit prompt             | `plans/audit/trading_system_audit_prompt.md` |
| Tested gate criteria     | plans_to_deployable_unified_audit § Phase 9  |
| Deployable gate criteria | plans_to_deployable_unified_audit § Phase 10 |
