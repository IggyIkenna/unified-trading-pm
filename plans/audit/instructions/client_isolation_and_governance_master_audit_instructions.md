---
doc_type: audit-instruction
title: client_isolation_and_governance_master_audit_instructions
summary:
  Weekly audit of per-client isolation + funds governance — one multiprocessing.Process per client under
  StrategySupervisor, CrossClientTransferForbiddenError at all 3 enforcement layers, assert_client_allowed() at every
  fund-movement boundary, UAC no-Any schema governance, jurisdiction (Odum UK vs Cayman) checks, and closure of the 6
  BLOCKING gaps from the 2026-05-20 retroactive audit.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: [audit, client-isolation, execution, governance, uac, data-correctness]
related: [../../archive/issues/cross_client_funds_isolation_retroactive_audit_2026_05_20.md]
created: 2026-05-22
tier: L4
parent_epic: client_isolation_and_governance_master
cadence: weekly (minimum)
verifier:
lifespan:
type: audit-instructions
epic: client_isolation_and_governance_master
assigned_vm: vm-cross-cutting
last_updated: 2026-05-22
---

# Client Isolation + Governance Master — Audit Instructions

## Epic Scope

Per-client subprocess isolation (`multiprocessing.Process` under `StrategySupervisor`), cross-client funds isolation
(HARD RULE: `CrossClientTransferForbiddenError` at 3 layers), jurisdiction (Odum UK vs Odum Group Cayman), share-class
reconciliation, UAC schema governance (no `Any` types). 6 BLOCKING gaps from 2026-05-20 retroactive audit must be
tracked to completion.

Codex SSOTs: `/codex/04-architecture/client-funds-isolation.md`,
`/codex/04-architecture/per-client-isolation-architecture.md`, `/codex/04-architecture/client-lifecycle-event-bus.md`

## Triggers

- Weekly (minimum cadence)
- After any transfer/rebalancing/bridge/sub-account code change
- After any UAC schema addition (check for `Any` type drift)
- After per-client isolation architecture changes

## Checklist

- [ ] (a) **One subprocess per client**: `StrategySupervisor` uses `multiprocessing.Process` for each client worker (not
      threads — ensures GIL-free crash isolation). Grep:
      `rg "multiprocessing.Process" strategy-service/ --include="*.py"` — verify used in supervisor, not threading

- [ ] (b) **CrossClientTransferForbiddenError at all 3 layers**: raised at UAC schema construction, strategy-service
      emit boundary, and execution-service consume boundary. Grep:
      `rg "CrossClientTransferForbiddenError" --include="*.py"` — verify 3 distinct call sites

- [ ] (c) **isolation_policy.assert_client_allowed() at transfer boundary**: every transfer/withdraw/deposit/bridge
      operation calls the isolation policy before executing. Grep: `rg "assert_client_allowed" --include="*.py"` —
      verify present at all fund movement boundaries

- [ ] (d) **UAC schema — no Any types**: `no-type-any-use-specific.mdc` rule passes across all UAC schema files. Grep:
      `rg "Any\b" unified-api-contracts/unified_api_contracts/ --include="*.py"` — review hits; `Any` from typing is
      banned; structural type alternatives required

- [ ] (e) **Jurisdiction check before flipping BLOCKED-JURISDICTION**: Odum Group Cayman covers venues that ban UK
      residents (Extended Starknet etc.); agents must check the Cayman list before marking BLOCKED-JURISDICTION. Read:
      `project_trading_entities.md` memory — verify Cayman entity list is current

- [ ] (f) **6 BLOCKING gaps from retroactive audit shipped**: all 6 items from
      `cross_client_funds_isolation_retroactive_audit_2026_05_20.md` are in code with commit SHAs. Check: the active
      plan absorbing those gaps — all `- [x]`

- [ ] (g) **UAC BATCH_EIA SOURCE_PRIORITY entry**: `BATCH_EIA` in `PipelineMode` has a corresponding `SOURCE_PRIORITY`
      entry. The `uac_batch_eia_missing_source_priority_2026_05_20.md` issue is resolved. Grep:
      `rg "BATCH_EIA" unified-api-contracts/ --include="*.py"` — verify SOURCE_PRIORITY entry present

- [ ] (h) **Alert on cross-client transfer attempt**: any attempted cross-client transfer fires an alert event (not just
      raises an error silently). Find: `rg "CrossClientEventError\|cross_client.*alert" --include="*.py"` — verify alert
      emitted

### E2E Cross-Cutting Verification

- (e2e-batch-live) **Batch-live round-trip**: pick one (venue, data_type) pair, run batch adapter → confirm manifest row
  → run live adapter → confirm same schema row. Requires only one working adapter pair, not all.
- (mock-upstream) **Independent audit**: cross-cutting audits MUST be runnable with `CLOUD_MOCK_MODE=true` to test
  infrastructure, error classification, and isolation patterns without real cloud access.

## Success Criteria

- All 8 checklist items GREEN
- Cross-client transfer impossible in all code paths (verified by tests at all 3 layers)
- UAC schema has zero `Any` types
- QG exits 0 for strategy-service, execution-service, and unified-api-contracts

## Output Format

Result file at `plans/audit/results/client_isolation_and_governance_master_audit_YYYY_MM_DD.md`. Same structure as per
`../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
