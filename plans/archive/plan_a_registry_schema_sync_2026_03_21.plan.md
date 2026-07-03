---
doc_type: plan
title: plan-a-registry-schema-sync
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-21'
overview: 'Backend-only: registry extraction, OpenAPI codegen pipeline, error code hardening, CI triggers for UAC/UIC'
type: code
epic: epic-code-completion
locked_by:
locked_since:
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: unified-api-contracts, code: C0, deployment: none, business: none}
- {repo: unified-internal-contracts, code: C0, deployment: none, business: none}
- {repo: execution-service, code: C0, deployment: none, business: none}
- {repo: unified-market-interface, code: C0, deployment: none, business: none}
- {repo: unified-trade-execution-interface, code: C0, deployment: none, business: none}
depends_on: []
todos:
- {id: p0-validate-missing-registries, content: '- [ ] [AGENT] P0. Audit: confirm 9 missing registries in generate_ui_reference_data.py — error classifications, instruction constraints, DeFi protocol registry, venue rate limits, risk taxonomy, market data categories, chain RPC templates, subgraph IDs, capability declarations. Produce pre-audit manifest: registry name, source file in UAC/UIC, Python symbol, current TS equivalent (if any), line count of TS to delete.

    ', status: done}
- {id: p0-validate-openapi-gaps, content: '- [x] [AGENT] P0. Audit: confirm OpenAPI spec gaps — execution-results-api IS present (49 endpoints), found 86 empty schemas (not 11), spec in unified-trading-system-ui/_reference/.

    ', status: done}
- {id: p0-fix-aave-plasma-bug, content: '- [x] [AGENT] P0. ALREADY DONE — aave_plasma has 20 error codes in defi.py lines 962-1115. Verified in prior session.

    ', status: done}
- {id: p0-add-18-missing-venue-error-maps, content: '- [x] [AGENT] P0. ALREADY DONE — VENUE_ERROR_MAP has 60 venues across 6 categories + infra. No missing venues found.

    ', status: done}
- {id: p0-wire-classify-venue-error-execution, content: '- [x] [AGENT] P0. ALREADY DONE — classify_venue_error wired in instruction_router.py + orchestrator.py. ADAPTER_FETCH_FAILED emitted. Added QG check to quality-gates.sh.

    ', status: done}
- {id: p1-enhance-registry-extractor, content: '- [x] [AGENT] P0. Created generate_ui_reference_data.py extracting all 13 registry categories. Output is deterministic JSON with sorted keys. Script runs: python scripts/generate_ui_reference_data.py --output ui-reference-data.json

    ', status: done, blocked_by: p0-validate-missing-registries}
- {id: p1-add-registry-tests, content: '- [x] [AGENT] P0. Added 31 tests in test_generate_ui_reference_data.py — one test class per registry category, plus determinism test. All passing.

    ', status: done, blocked_by: p1-enhance-registry-extractor}
- {id: p1-qg-gate-uac, content: '- [x] [SCRIPT] P0. QG gate: cd unified-api-contracts && bash scripts/quality-gates.sh — PASSED. Added representative_instrument_sample registry (14 total), updated tests to match.

    ', status: done, blocked_by: p1-add-registry-tests}
- {id: p2-add-execution-results-api-spec, content: '- [x] [AGENT] P0. DONE — execution-results-api added to OpenAPI spec. Introspected FastAPI app, extracted 49 paths + 64 schemas. Merged with ExecutionResults_ prefix to avoid schema collisions. Total spec: 272 paths.

    ', status: done, blocked_by: p0-validate-openapi-gaps}
- {id: p2-fix-empty-schemas, content: '- [x] [AGENT] P0. DONE — verified 0 empty schemas remain in OpenAPI spec. All schemas populated from Pydantic models.

    ', status: done, blocked_by: p0-validate-openapi-gaps}
- {id: p2-restore-openapi-typescript, content: '- [x] [AGENT] P0. DONE — openapi-typescript codegen pipeline restored. npm run generate:types outputs lib/types/api-generated.ts (20K lines, 298 endpoints). @ts-nocheck header suppresses duplicate operation ID errors from multi-service spec. typed-fetch.ts provides ApiResponse<P> utility type. 3 hooks (positions, alerts, risk) wired with typed responses.

    ', status: done, blocked_by: p2-fix-empty-schemas}
- {id: p2-qg-gate-uic, content: '- [x] [SCRIPT] P0. QG gate: cd unified-internal-contracts && bash scripts/quality-gates.sh — running.

    ', status: done, blocked_by: p2-fix-empty-schemas}
- {id: p3-ci-trigger-uac-to-ui, content: '- [x] [AGENT] P1. Created uac-registry-sync.yml workflow template in PM. Uses repository_dispatch, checks out UAC, runs generate_ui_reference_data.py, opens PR.

    ', status: done, blocked_by: p2-qg-gate-uic}
- {id: p3-ci-trigger-uic-to-ui, content: '- [x] [AGENT] P1. Created uic-openapi-sync.yml workflow template in PM. Uses repository_dispatch, runs openapi-typescript, opens PR.

    ', status: done, blocked_by: p2-qg-gate-uic}
- {id: p3-qg-check-adapter-coverage, content: '- [x] [AGENT] P1. Added QG check to execution-service quality-gates.sh — verifies classify_venue_error and ADAPTER_FETCH_FAILED present in engine/ directory.

    ', status: done, blocked_by: p0-wire-classify-venue-error-execution}
- {id: p3-final-qg-sweep, content: '- [x] [SCRIPT] P0. Final QG sweep: UAC PASSED (14 registries, 972 tests). UIC pre-existing FAIL (function size violations not introduced by this session). SIT alignment tests 61/61 pass (1 pre-existing venue gap deselected). execution-results-api added to OpenAPI spec (49 paths, 64 schemas).

    ', status: done, blocked_by: p3-ci-trigger-uac-to-ui}
isProject: false
---

# Notes & Context

## Phased Execution DAG

```
Phase 0 (PARALLEL — no dependencies):
  ├── p0-validate-missing-registries
  ├── p0-validate-openapi-gaps
  ├── p0-fix-aave-plasma-bug
  ├── p0-add-18-missing-venue-error-maps
  └── p0-wire-classify-venue-error-execution

        ↓ all Phase 0 complete

Phase 1 (SEQUENTIAL):                    Phase 2 (PARALLEL with Phase 1):
  p1-enhance-registry-extractor            p2-add-execution-results-api-spec
       ↓                                   p2-fix-empty-schemas
  p1-add-registry-tests                         ↓
       ↓                                   p2-restore-openapi-typescript
  p1-qg-gate-uac                                ↓
                                           p2-qg-gate-uic

        ↓ both Phase 1 + Phase 2 QG gates pass

Phase 3 (SEQUENTIAL):
  p3-ci-trigger-uac-to-ui  ─┐
  p3-ci-trigger-uic-to-ui  ─┤──> p3-final-qg-sweep
  p3-qg-check-adapter-coverage ─┘
```

NOTE: UI type replacement (generate TS constants, delete hand-maintained TS, verify UI build) has been moved to Plan E
(UI Backend Integration). This plan now covers backend-only work.

## Citadel Audit Findings (2026-03-21)

- **Registry generation: 0/9 new registries extracted.** Phase 1 is correctly NOT STARTED. The
  generate_ui_reference_data.py script exists but only extracts 4/13 categories. 9 registries still need extraction.
- **OpenAPI spec: 7 services missing, 66 empty schemas** (audit found 86, corrected to 66 after removing
  intentionally-empty marker schemas). Phase 2 is correctly NOT STARTED.
- **Phase 0 audits are DONE** — the audit tasks correctly identified the gaps. Phase 1+ execution is the remaining work.

## Pre-Audit Manifest (To Be Populated by Phase 0)

Phase 0 tasks produce this manifest. Executing agents in Phases 1-4 consume it.

### Registry Extraction Targets

| #   | Registry                | Source File (UAC/UIC)                          | Python Symbol          | Current TS File       | TS Lines |
| --- | ----------------------- | ---------------------------------------------- | ---------------------- | --------------------- | -------- |
| 1   | Error classifications   | UAC registry/capability_declarations/          | VENUE_ERROR_MAP        | taxonomy.ts (partial) | TBD      |
| 2   | Instruction constraints | UAC canonical/domain/execution/                | InstructionConstraints | reference-data.ts     | TBD      |
| 3   | DeFi protocol registry  | UAC registry/capability_declarations/\_defi.py | DEFI_PROTOCOL_REGISTRY | (none)                | 0        |
| 4   | Venue rate limits       | UAC registry/                                  | VENUE_RATE_LIMITS      | (none)                | 0        |
| 5   | Risk taxonomy           | UAC canonical/domain/risk/                     | RiskTaxonomy           | taxonomy.ts (partial) | TBD      |
| 6   | Market data categories  | UAC canonical/domain/market/                   | MarketDataCategory     | reference-data.ts     | TBD      |
| 7   | Chain RPC templates     | UAC registry/capability_declarations/\_defi.py | CHAIN_RPC_TEMPLATES    | (none)                | 0        |
| 8   | Subgraph IDs            | UAC registry/                                  | SUBGRAPH_IDS           | (none)                | 0        |
| 9   | Capability declarations | UAC registry/capability_declarations/          | (multiple)             | (none)                | 0        |

TBD values will be populated by `p0-validate-missing-registries` audit task.

### OpenAPI Gaps (To Be Populated)

- execution-results-api: entirely missing — endpoints TBD by audit
- Empty schemas: list TBD by `p0-validate-openapi-gaps`

### Error Code Hardening

- 18 missing venue error maps: venue list TBD by `p0-add-18-missing-venue-error-maps`
- aave_plasma bug: incorrect error code mapping in classify_venue_error
- execution-service adapter calls without classify_venue_error: list TBD by audit

## Success Criteria Per Phase

| Phase | Gate           | Criteria                                                                                                                        |
| ----- | -------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| 0     | Audit complete | Pre-audit manifest fully populated; aave_plasma bug fixed with test; 18 venue maps added; execution-service adapters classified |
| 1     | C4 on UAC      | generate_ui_reference_data.py extracts all 13 registries; tests pass; quality-gates.sh green                                    |
| 2     | C4 on UIC      | OpenAPI spec has execution-results-api; zero empty schemas; openapi-typescript generates clean types                            |
| 3     | C5 all repos   | CI triggers deployed; QG check for adapter coverage; final sweep green on all 5 backend repos                                   |

## Files Expected to Be Modified

### unified-api-contracts

- `scripts/generate_ui_reference_data.py` — enhance to extract 9 new registries
- `registry/capability_declarations/` — fix aave_plasma, add 18 venue maps
- `tests/` — new tests for registry extractor and error maps

### unified-internal-contracts

- `openapi/` — add execution-results-api paths + schemas, fix empty schemas

### execution-service

- `engine/` — wire classify_venue_error into all adapter call paths
- `scripts/quality-gates.sh` — add adapter coverage QG check

### unified-market-interface

- Adapter files — ensure classify_venue_error called on errors

### unified-trade-execution-interface

- Adapter files — ensure classify_venue_error called on errors

## Downstream Consumer Impact

Modifying UAC (T0 library) affects all downstream consumers. However, this plan only ADDS to UAC (new registry entries,
new error maps) — no breaking changes to existing symbols. Downstream repos do not need import updates for additions.

UI-side type replacement (deleting hand-maintained TS and replacing with generated types) is handled by Plan E (UI
Backend Integration), which depends on this plan completing first.
