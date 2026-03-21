---
name: plan-a-registry-schema-sync
overview: "Backend-only: registry extraction, OpenAPI codegen pipeline, error code hardening, CI triggers for UAC/UIC"
type: code
epic: epic-code-completion
status: active
locked_by: null
locked_since: null
completion_gates:
  code: C5
  deployment: none
  business: none
repo_gates:
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-internal-contracts
    code: C0
    deployment: none
    business: none
  - repo: execution-service
    code: C0
    deployment: none
    business: none
  - repo: unified-market-interface
    code: C0
    deployment: none
    business: none
  - repo: unified-trade-execution-interface
    code: C0
    deployment: none
    business: none
depends_on: []
todos:
  # ── Phase 0: Audit Validation + Error Code Fixes (PARALLEL) ──
  - id: p0-validate-missing-registries
    content: |
      - [ ] [AGENT] P0. Audit: confirm 9 missing registries in generate_ui_reference_data.py — error classifications, instruction constraints, DeFi protocol registry, venue rate limits, risk taxonomy, market data categories, chain RPC templates, subgraph IDs, capability declarations. Produce pre-audit manifest: registry name, source file in UAC/UIC, Python symbol, current TS equivalent (if any), line count of TS to delete.
    status: todo
  - id: p0-validate-openapi-gaps
    content: |
      - [ ] [AGENT] P0. Audit: confirm OpenAPI spec gaps — execution-results-api missing entirely, list all empty schemas (expect ~11), identify any path/schema mismatches against actual API route definitions in the 9 API repos.
    status: todo
  - id: p0-fix-aave-plasma-bug
    content: |
      - [ ] [AGENT] P0. Fix aave_plasma bug in UAC error classifier. The classify_venue_error function incorrectly maps aave_plasma errors. Fix the mapping in unified_api_contracts registry/capability_declarations. Add unit test for the corrected mapping.
    status: todo
  - id: p0-add-18-missing-venue-error-maps
    content: |
      - [ ] [AGENT] P0. Add 18 missing venue error maps to VENUE_ERROR_MAP in UAC. Each venue adapter that calls classify_venue_error must have its venue key present. Identify all 18 missing venues from the adapter list, add error maps with at minimum: connection_error, rate_limit, auth_failure, unknown_error codes.
    status: todo
  - id: p0-wire-classify-venue-error-execution
    content: |
      - [ ] [AGENT] P0. Wire classify_venue_error into execution-service for all adapter calls. Every adapter fetch path must call classify_venue_error and emit ADAPTER_FETCH_FAILED events on error. Audit execution-service/engine/ for any adapter call that catches exceptions without classification.
    status: todo
  # ── Phase 1: Registry Generation Script Enhancement (SEQUENTIAL after Phase 0) ──
  - id: p1-enhance-registry-extractor
    content: |
      - [ ] [AGENT] P0. Enhance generate_ui_reference_data.py to extract all 13 registry categories (4 existing + 9 new). Each registry must produce a JSON section in ui-reference-data.json with: registry_name, version (from source repo pyproject.toml), entries (list of typed objects). Output must be deterministic (sorted keys, stable ordering) so CI diffs are meaningful.
    status: todo
    blocked_by: p0-validate-missing-registries
  - id: p1-add-registry-tests
    content: |
      - [ ] [AGENT] P0. Add tests for the enhanced registry extractor — one test per registry category verifying: output schema matches expected shape, no empty entries, all enum values present, version field populated. Tests must use the repo .venv via quality-gates.sh.
    status: todo
    blocked_by: p1-enhance-registry-extractor
  - id: p1-qg-gate-uac
    content: |
      - [ ] [SCRIPT] P0. QG gate: cd unified-api-contracts && bash scripts/quality-gates.sh — must pass before Phase 2 starts.
    status: todo
    blocked_by: p1-add-registry-tests
  # ── Phase 2: OpenAPI Spec Fixes + Codegen Pipeline (PARALLEL with Phase 1) ──
  - id: p2-add-execution-results-api-spec
    content: |
      - [ ] [AGENT] P0. Add execution-results-api to OpenAPI spec. Introspect execution-results-api route definitions (FastAPI/Flask) and generate the corresponding OpenAPI paths + schemas. Must cover all endpoints that the 3 UIs (execution-analytics-ui, trading-analytics-ui, batch-audit-ui) consume.
    status: todo
    blocked_by: p0-validate-openapi-gaps
  - id: p2-fix-empty-schemas
    content: |
      - [ ] [AGENT] P0. Fix all empty schemas in OpenAPI spec. For each empty {} schema identified in Phase 0 audit, populate with the actual response model from the corresponding API repo's Pydantic/dataclass definitions. Cross-reference with UIC/UAC canonical types where applicable.
    status: todo
    blocked_by: p0-validate-openapi-gaps
  - id: p2-restore-openapi-typescript
    content: |
      - [ ] [AGENT] P0. Restore openapi-typescript codegen pipeline in unified-trading-system-ui. The script exists but output is in a .bak file. Fix: update the codegen script to output to src/generated/api-types.ts (not .bak), run it against the corrected OpenAPI spec, verify generated types compile with tsc --noEmit.
    status: todo
    blocked_by: p2-fix-empty-schemas
  - id: p2-qg-gate-uic
    content: |
      - [ ] [SCRIPT] P0. QG gate: cd unified-internal-contracts && bash scripts/quality-gates.sh — must pass before Phase 3 starts.
    status: todo
    blocked_by: p2-fix-empty-schemas
  # ── Phase 3: CI/CD Triggers + QG Enforcement (SEQUENTIAL after Phases 1+2) ──
  - id: p3-ci-trigger-uac-to-ui
    content: |
      - [ ] [AGENT] P1. Create GitHub Actions workflow: on UAC commit to main/staging, trigger registry regeneration. Workflow runs generate_ui_reference_data.py + generate-ts-from-registry, commits updated JSON + TS to a PR branch on unified-trading-system-ui, opens PR with diff summary. Use repository_dispatch or workflow_dispatch pattern consistent with existing cascade infrastructure.
    status: todo
    blocked_by: p2-qg-gate-uic
  - id: p3-ci-trigger-uic-to-ui
    content: |
      - [ ] [AGENT] P1. Create GitHub Actions workflow: on UIC commit to main/staging, trigger OpenAPI codegen. Workflow runs openapi-typescript against updated spec, commits generated api-types.ts to PR branch on unified-trading-system-ui, opens PR. Similar pattern to UAC trigger above.
    status: todo
    blocked_by: p2-qg-gate-uic
  - id: p3-qg-check-adapter-coverage
    content: |
      - [ ] [AGENT] P1. Add QG check to execution-service quality-gates.sh: verify every adapter that calls classify_venue_error has its venue key present in VENUE_ERROR_MAP. Script should grep adapter files for classify_venue_error calls, extract venue names, and check against VENUE_ERROR_MAP keys. Fail if any venue is missing.
    status: todo
    blocked_by: p0-wire-classify-venue-error-execution
  - id: p3-final-qg-sweep
    content: |
      - [ ] [SCRIPT] P0. Final QG sweep across all 5 backend repos: unified-api-contracts, unified-internal-contracts, execution-service, unified-market-interface, unified-trade-execution-interface. Run quality-gates.sh on each.
    status: todo
    blocked_by: p3-ci-trigger-uac-to-ui
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
