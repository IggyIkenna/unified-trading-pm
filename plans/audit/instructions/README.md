# Audit Instructions — per-epic templates

Each file in this directory is the **everlasting audit instruction template** for one of the 19 epics. These files tell
you *how* to audit an epic's code surface — what to check, when to check it, and what "green" looks like.

**Format and lifecycle**: see [`../README.md`](../README.md).

**Rule**: when a new epic is created in `plans/epics/`, create a matching `<epic_slug>_audit_instructions.md` here in
the same commit. Missing instruction files are review-blocking.

**Never archive these files.** Update them when epic scope changes or new invariants are codified.

## Current instruction files (19 epics)

| Epic slug | Tier | Assigned VM | File |
|-----------|------|-------------|------|
| `defi_master` | L0 | `vm-defi` | [defi_master_audit_instructions.md](defi_master_audit_instructions.md) |
| `cefi_master` | L0 | `vm-cefi` | [cefi_master_audit_instructions.md](cefi_master_audit_instructions.md) |
| `tradfi_master` | L0 | `vm-tradfi` | [tradfi_master_audit_instructions.md](tradfi_master_audit_instructions.md) |
| `sports_master` | L0 | `vm-sports` | [sports_master_audit_instructions.md](sports_master_audit_instructions.md) |
| `predictions_master` | L0 | `vm-prediction` | [predictions_master_audit_instructions.md](predictions_master_audit_instructions.md) |
| `instruments_master` | L1 | `vm-cefi` (co-located) | [instruments_master_audit_instructions.md](instruments_master_audit_instructions.md) |
| `mtds_mdps_master` | L1 | `vm-ml` | [mtds_mdps_master_audit_instructions.md](mtds_mdps_master_audit_instructions.md) |
| `features_and_ml_master` | L1 | `vm-ml` | [features_and_ml_master_audit_instructions.md](features_and_ml_master_audit_instructions.md) |
| `manifest_master` | L1 | `vm-defi` (co-located) | [manifest_master_audit_instructions.md](manifest_master_audit_instructions.md) |
| `strategy_master` | L2 | `vm-trading-core` | [strategy_master_audit_instructions.md](strategy_master_audit_instructions.md) |
| `execution_master` | L2 | `vm-trading-core` | [execution_master_audit_instructions.md](execution_master_audit_instructions.md) |
| `trading_agent_master` | L2 | `vm-trading-core` | [trading_agent_master_audit_instructions.md](trading_agent_master_audit_instructions.md) |
| `dart_and_promote_master` | L3 | `vm-operator-ops` | [dart_and_promote_master_audit_instructions.md](dart_and_promote_master_audit_instructions.md) |
| `deployment_and_user_management_master` | L3 | `vm-operator-ops` | [deployment_and_user_management_master_audit_instructions.md](deployment_and_user_management_master_audit_instructions.md) |
| `infrastructure_master` | L4 | `vm-cross-cutting` | [infrastructure_master_audit_instructions.md](infrastructure_master_audit_instructions.md) |
| `observability_master` | L4 | `vm-cross-cutting` | [observability_master_audit_instructions.md](observability_master_audit_instructions.md) |
| `batch_live_symmetry_master` | L4 | `vm-cross-cutting` | [batch_live_symmetry_master_audit_instructions.md](batch_live_symmetry_master_audit_instructions.md) |
| `client_isolation_and_governance_master` | L4 | `vm-cross-cutting` | [client_isolation_and_governance_master_audit_instructions.md](client_isolation_and_governance_master_audit_instructions.md) |
| `orchestrator_master` | L5 | `vm-orchestrator` | [orchestrator_master_audit_instructions.md](orchestrator_master_audit_instructions.md) |
