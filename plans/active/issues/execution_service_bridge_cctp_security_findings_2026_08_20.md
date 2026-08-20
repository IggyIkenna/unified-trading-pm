---
doc_type: issue
title: Execution-service bridge and CCTP security findings
summary: Actionable remediation for the bridge.py and cctp.py findings from W15.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service]
scope: [engineer]
tags: [execution, security, bridge, cctp, w15]
related:
  [
    /plans/active/w15_execution_service_venue_adaptor_security_audit_2026_08_20.md,
    /plans/epics/system_readiness_master.md,
  ]
created: 2026-08-20
author: slot-5
parent_epic: system_readiness_master
priority: P0
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
context_scope:
  [
    execution-service/execution_service/defi_execution/protocols/bridge.py,
    execution-service/execution_service/defi_execution/protocols/cctp.py,
  ]
source:
  - /plans/active/w15_execution_service_venue_adaptor_security_audit_2026_08_20.md
---

# Execution-service bridge and CCTP security findings

## What I found

- `execution_service/defi_execution/protocols/bridge.py` logs a prefix of the Socket API key, accepts unchecked
  amounts and recipients, silently treats unknown tokens as native currency, signs aggregator-supplied transaction
  targets/calldata without a local safety check, and broadcasts without caller-controlled slippage/deadline bounds.
- `execution_service/defi_execution/protocols/bridge.py` creates a new transfer UUID on every retry and has no durable
  idempotency/source-transaction record.
- `execution_service/defi_execution/protocols/cctp.py` falls back to the destination recipient when source wallet
  credentials are absent, converts unchecked amounts to micro-USDC, accepts malformed recipient strings, and keeps
  transfer state only in process memory.
- `execution_service/defi_execution/protocols/cctp.py` looks up a bridge-tx-hash as though it were a transfer ID,
  so a valid source transaction cannot be resolved by `get_bridge_status()`; attestation timeout and terminal failure
  semantics are incomplete.

## Why it matters

These paths can sign irreversible cross-chain transactions. Unbounded or unchecked aggregator calldata, invalid
recipient/amount inputs, duplicate burn submissions, and status failures can move or burn funds while leaving the
caller with an incorrect or incomplete execution state.

## Recommended decision

Implement and test the bounded fixes below before enabling these live write paths for unattended execution. Keep the
existing W15 checklist record and resolve each high-severity item with a landed SHA or an explicitly operator-gated
follow-up.

- [x] ✅ [BACKEND] P0. Add strict bridge amount, recipient, token, chain, aggregator target/calldata, credential, and
      caller slippage/deadline validation in `bridge.py` (repo: execution-service). — execution-service@fb50f7296; Evidence: landed on origin/live-defi-rollout; compileall passed.
- [x] ✅ [BACKEND] P0. Add durable idempotency and source-transaction tracking for Socket bridge retries in `bridge.py`
      (repo: execution-service). — execution-service@ef899bf5b8; Evidence: quality-gates=8816 passed, 22 skipped, 1 xpassed.
- [x] ✅ [BACKEND] P0. Add CCTP amount/recipient validation and fail closed when source wallet credentials are absent
      before approve/burn (repo: execution-service). — execution-service@fb50f7296a; Evidence: tests=8827 passed, 22 skipped, 1 xpassed; quality-gates=exit1 on pre-existing remote method-size/fallback-baseline debt, no CCTP test failure.
- [ ] [BACKEND] P0. Make CCTP burn tracking durable and idempotent, preserve the source burn transaction hash, and
      prevent duplicate approve/burn submissions on retry (repo: execution-service).
- [ ] [BACKEND] P0. Correct CCTP status lookup to resolve source transaction hashes and enforce attestation timeout
      and terminal failure semantics (repo: execution-service).
