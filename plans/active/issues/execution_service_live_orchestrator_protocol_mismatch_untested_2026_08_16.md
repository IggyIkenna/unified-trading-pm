---
doc_type: issue
title: execution-service's production live-execution orchestrator may not structurally satisfy the LiveOrchestrator protocol it's cast to — untested end-to-end
summary: >-
  Surfaced as a side-discovery while building the W1 external instruction-submission surface (a sub-agent needed a
  real, non-mocked LiveOrchestrator-protocol implementation for its test and found the production lazy-orchestrator
  doesn't fit the protocol it's cast to). Not independently re-derived in full here — the cited function location was
  spot-checked and exists; the protocol-mismatch and return-type claims are relayed from the sub-agent's
  investigation, not re-verified line-by-line.
status: open
nature: notes
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service]
scope: [engineer]
tags: [execution, live-orchestrator, protocol-mismatch, untested, matching-engine]
related:
  [
    /plans/active/nick_ai_platform_readiness_remediation_2026_08_16.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
  ]
created: 2026-08-16
source: >-
  Side-discovery during nick_ai_platform_readiness_remediation_2026_08_16.md's W1 execution-service todo — the
  sub-agent needed a real (non-mock) LiveOrchestrator to prove its instruction-submission surface reaches a real
  fill, and in doing so found the actual production orchestrator doesn't satisfy the protocol.
parent_epic: security_and_cross_cutting_master
priority: P1
assigned_vm: NA
assigned_role: backend_engineer
effort: medium
locked_by:
resolved_by:
context_scope: [/plans/active/nick_ai_platform_readiness_remediation_2026_08_16.md, execution-service/execution_service/cli/handlers/live_execution_handler.py, execution-service/execution_service/orchestration/orchestrator.py]
execution_scope: local-only
drift_direction: advance-code
depends_on: []
---

# execution-service's live-execution orchestrator: protocol mismatch, untested end-to-end

## What was found

`execution_service/cli/handlers/live_execution_handler.py::_create_orchestrator_for_venue` (confirmed to exist at
this location, line ~332, with a second call site at line 851) constructs an `ExecutionOrchestrator` for the
production live-execution path. Per the reporting sub-agent's investigation: this concrete class does **not**
structurally satisfy the `LiveOrchestrator` protocol it gets cast to elsewhere in the codebase (e.g.
`ManualOperationHandler.execute()`'s expected interface) — it accepts a **different instruction type** than the
protocol declares, and its execute-equivalent method **returns `None`, not a `dict`** as the protocol's callers
expect.

**Why this has gone unnoticed**: every existing test that exercises this path **mocks** the orchestrator rather than
using a real implementation. The mismatch only surfaced because the W1 remediation sub-agent needed a genuinely
real (non-mock) `LiveOrchestrator` implementation for its own instruction-submission-surface test, and the real
production one didn't fit.

## Why this matters

If accurate, this means the production live-execution code path — the one that actually places real orders — is
**untested end-to-end against its own real implementation**, and the protocol mismatch could mean a live instruction
silently fails to produce the expected result shape somewhere downstream (a caller expecting a `dict` receiving
`None`). This is squarely in the live-trading blast radius, not a cosmetic typing issue, if the claim holds up under
full verification.

## What's not yet done

- [x] ✅ [AGENT] P1. Extracted to `cross_cutting_satellite_ao_dispatch_batch14_2026_08_17.md` item 12 (na-eligibility-audit 2026-08-17). **Independently verify the protocol mismatch** — read `ExecutionOrchestrator`'s actual method
      signature against the `LiveOrchestrator` protocol definition directly (do not trust this doc's relay alone),
      confirm the instruction-type and return-type mismatch claims with a direct citation of both sides.
- [x] ✅ [AGENT] P1. Extracted to `cross_cutting_satellite_ao_dispatch_batch14_2026_08_17.md` item 13 (na-eligibility-audit 2026-08-17). **If confirmed, determine blast radius** — trace every call site that casts to `LiveOrchestrator`
      and would receive an `ExecutionOrchestrator` instance in production, and check whether a `None` return where a
      `dict` is expected would raise, silently no-op, or corrupt downstream state.
- [x] ✅ [AGENT] P1. Extracted to `cross_cutting_satellite_ao_dispatch_batch14_2026_08_17.md` item 14 (na-eligibility-audit 2026-08-17). **Add a real (non-mock) end-to-end test** of the production live-execution path, matching the
      pattern the W1 sub-agent's own test used (`tests/unit/test_external_instruction_api.py` in
      `execution-service`, per `nick_ai_platform_readiness_remediation_2026_08_16.md`'s W1 evidence) — a real
      `LiveOrchestrator`-conformant implementation exercised end-to-end, not a mock standing in for the interface
      contract itself.
- [ ] [AGENT] P2. **Fix the mismatch** (either widen the protocol to match the real return/instruction shape, or fix
      `ExecutionOrchestrator` to genuinely conform) once the above confirms the real shape of the problem — do not
      guess the fix before the trace above is done.

## Progress Log

**2026-08-16 — filed.** Relayed from the W1 execution-service remediation sub-agent's final report (part of
`nick_ai_platform_readiness_remediation_2026_08_16.md`); the cited function's existence and location were spot-
checked directly (confirmed), the protocol-mismatch and return-type claims were not independently re-derived before
filing — see the todos above for that verification work. Flagged to the operator in the same turn this was filed,
per the workspace's big-finding notification rule (cross-cutting to live execution correctness).
**context-scout 2026-08-17**: populated/refreshed context_scope (3 entries)
- **na-eligibility-audit 2026-08-17** [body-hash:3655dacfb7f13e16]: RECLASSIFY (per-todo split) -- extracted 3 of 4 open items (independently verify the protocol mismatch, determine blast radius if confirmed, add a real end-to-end test) to cross_cutting_satellite_ao_dispatch_batch14_2026_08_17.md items 12-14. Doc stays assigned_vm: NA for its 1 remaining item ('Fix the mismatch') -- genuinely gated on the diagnosis outcome (widen the protocol vs fix the implementation), not bounded standalone. Cross-cutting tranche audit.
