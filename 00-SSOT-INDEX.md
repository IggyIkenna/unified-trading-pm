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

| Doc                | Location                                                        |
| ------------------ | --------------------------------------------------------------- |
| Workspace manifest | `workspace-manifest.json`                                       |
| Topology DAG       | `WORKSPACE_MANIFEST_DAG.svg`                                    |
| Runtime topology   | `../deployment-service/configs/runtime-topology.yaml`           |
| Checklist template | `../deployment-service/configs/checklist.template.service.yaml` |

## Audit and Gates

| Doc                      | Location                                           |
| ------------------------ | -------------------------------------------------- |
| Audit prompt             | `plans/active/trading_system_audit_prompt.plan.md` |
| Tested gate criteria     | plans_to_deployable_unified_audit § Phase 9        |
| Deployable gate criteria | plans_to_deployable_unified_audit § Phase 10       |
