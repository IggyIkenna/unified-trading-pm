---
doc_type: codex-ssot
title: Schema Placement Rules
summary:
  Type-placement rules — a type imported by 2+ repos lives in UAC (external-data) or UIC (cross-service internal
  contract), never a service; services own internal processing-state types only. Includes the 4-step decision flow +
  DeFi type-to-owner placement matrix.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [uac, contracts, ssot, schema, type-placement]
related:
  [
    /codex/04-architecture/schema-versioning.md,
    /codex/02-data/contracts-scope-and-layout.md,
    /codex/04-architecture/separation-of-concerns.md,
  ]
created: 2026-03-27
authoritative_for: [schema placement rules (which repo owns a type), UAC-external-vs-UIC-internal type ownership matrix]
referenced_by: [/codex/04-architecture/schema-versioning.md, /codex/04-architecture/separation-of-concerns.md]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Schema Placement Rules

## Principle

Types and schemas belong in ONE place. If 2+ repos import a type, it belongs in a contracts library (UIC or UAC), not in
a service. Services own only their internal processing state types.

## Ownership Matrix

### UAC internal (unified_api_contracts.internal) — Cross-Service Contracts

`unified_api_contracts.internal` owns types that flow between services via events, instructions, or shared state:

- **Execution types**: `OperationType`, `OrderType`, `PositionType`, `PositionSide`, `InstructionType`, `BenchmarkType`
- **Execution results**: `ExecutionResult`, `SignalExecutionResult`, `ServiceExecutionStatus`
- **Execution instructions**: `ExecutionInstruction`
- **DeFi results**: `DeFiSwapResult`, `CeFiOrderFill`, `FlashLoanResult`
- **Alerts**: `DefiAlert`, `AlertSeverity`
- **TypedDicts**: shared structured payloads consumed by 2+ services

### UAC (unified-api-contracts) — External Data Classifications

UAC owns types that classify, normalize, or route external data:

- **Error codes**: `DefiErrorCode` (13 structured codes — FAIL/RETRY/SKIP prefix)
- **Alert types**: `DefiAlertType`
- **Data sources**: `DeFiDataSource`
- **Chain infrastructure**: `CHAIN_RPC_TEMPLATES`, `SUBGRAPH_IDS`
- **Venue capabilities**: `capability_declarations/` registry
- **External API schemas**: `external/{source}/schemas.py`

### Services — Internal Types Only

Services own types that never cross service boundaries:

- Config models (Pydantic `Settings` classes)
- Internal processing state (job tracking, batch progress)
- CLI argument models
- Private helper dataclasses

## Decision Flow

1. Does 2+ repos import this type? --> UIC (internal contracts) or UAC (external data)
2. Does it classify/normalize external API data? --> UAC `external/{source}/`
3. Does it define cross-service execution semantics? --> UIC `domain/{service}/`
4. Is it service-internal only? --> Keep in the service, clearly marked as internal

## Anti-Patterns

- Defining an enum in a service that other services also need (move to UIC)
- Re-declaring a UAC error code in a service instead of importing it
- Putting internal service state into UIC (over-sharing)
- Inline TypedDicts in service code that duplicate UIC contract types
- Services importing from `unified_api_contracts.canonical.*` or `unified_api_contracts.normalize_utils.*` (UAC
  internals)

## DeFi-Specific Placement

| Type                   | Owner | Path                                        |
| ---------------------- | ----- | ------------------------------------------- |
| `DefiErrorCode`        | UAC   | `canonical/domain/defi.py`                  |
| `DefiAlertType`        | UAC   | `canonical/domain/defi.py`                  |
| `DeFiDataSource`       | UAC   | `canonical/domain/defi.py`                  |
| `CHAIN_RPC_TEMPLATES`  | UAC   | `registry/capability_declarations/_defi.py` |
| `DeFiSwapResult`       | UIC   | `domain/execution/`                         |
| `FlashLoanResult`      | UIC   | `domain/execution/`                         |
| `DefiAlert`            | UIC   | `domain/alerts/`                            |
| `ExecutionInstruction` | UIC   | `domain/execution/`                         |

## Reference

- UAC layout: `unified-trading-pm/codex/02-data/contracts-scope-and-layout.md`
- Interface credential convention: `unified-trading-pm/codex/04-architecture/interface-credential-convention.md`
