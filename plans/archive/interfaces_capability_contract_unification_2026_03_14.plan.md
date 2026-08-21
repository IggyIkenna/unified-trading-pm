---
doc_type: plan
title: interfaces-capability-contract-unification-2026-03-14
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-14'
overview: 'Unify architecture, import policy, capability registry, and runtime guardrails across all interface repos and their consuming services. Standardize raw->validated->canonical flows, endpoint selection by mode/env/auth scope, and fail-fast errors for unsupported mode/provider/key combinations.

  '
type: mixed
epic: epic-code-completion
completion_gates: {code: C5, deployment: D3, business: none}
repo_gates:
- {repo: unified-api-contracts, code: C0, deployment: none, business: none, readiness_note: Canonical provider capability and endpoint metadata SSOT.}
- {repo: unified-market-interface, code: C0, deployment: none, business: none, readiness_note: Market data adapters consume capability registry + canonical contracts.}
- {repo: unified-reference-data-interface, code: C0, deployment: none, business: none, readiness_note: Reference data adapters aligned to same selection/guardrail model.}
- {repo: unified-trade-execution-interface, code: C0, deployment: none, business: none, readiness_note: Execution adapters aligned to mode/env/auth capability checks.}
- {repo: unified-sports-execution-interface, code: C0, deployment: none, business: none, readiness_note: Sports adapters aligned to same capability/normalization flow.}
- {repo: unified-defi-execution-interface, code: C0, deployment: none, business: none, readiness_note: Protocol adapters aligned to same capability/normalization flow.}
- {repo: unified-position-interface, code: C0, deployment: none, business: none, readiness_note: Position providers aligned to capability-aware adapter contracts.}
- {repo: unified-feature-calculator-library, code: C0, deployment: none, business: none, readiness_note: Feature-domain capability contracts consumed by services.}
- {repo: unified-internal-contracts, code: C0, deployment: none, business: none, readiness_note: Internal cross-service contracts remain separated from external provider schemas.}
- {repo: unified-domain-client, code: C0, deployment: none, business: none, readiness_note: Service-facing client APIs consume capability checks consistently.}
- {repo: unified-trading-library, code: C0, deployment: none, business: none, readiness_note: Shared guardrail helpers + error taxonomy utilities.}
- {repo: unified-trading-codex, code: C0, deployment: none, business: none, readiness_note: 'SSOT docs for ownership, flows, and capability semantics.'}
- {repo: unified-trading-pm, code: C0, deployment: none, business: none, readiness_note: 'Rollout orchestration, validators, and policy enforcement.'}
depends_on: []
supersedes: [uac-uic-umi-contract-surface-refactor-2026-03-14]
todos:
- {id: step0-register-plan, content: '- [ ] [AGENT] P0. Add plan to INDEX.md under "Interface Capability Unification" section. Verify no slug conflict with existing plans.

    ', status: todo}
- {id: p0-capability-schema, content: '- [ ] [AGENT] P0. Define capability registry schema in unified-api-contracts. Required fields: provider, domain, operation, supports_live, supports_batch, supports_historical, supports_testnet, supports_mainnet, requires_auth, auth_scope, data_latency, allowed_instruments, rate_limit_tier, endpoint_by_environment, endpoint_by_mode, deprecation_status.

    ', status: todo}
- {id: p0-backfill-providers, content: '- [ ] [AGENT] P0. Backfill capability registry with all current providers/endpoints/operations from tradfi, sports, defi, reference data, positions, execution domains.

    ', status: todo}
- {id: p1-registry-population, content: '- [ ] [AGENT] P1. Populate mode/env/auth support metadata for tradfi, sports, defi, reference data, positions, execution. Ensure endpoint_by_environment and endpoint_by_mode are complete for all active providers.

    ', status: todo}
- {id: p2-error-classes, content: '- [ ] [AGENT] P2. Add fail-fast error classes to unified-trading-library: UnsupportedModeError, UnsupportedEnvironmentError, ApiKeyScopeMismatchError, UnsupportedOperationError, CapabilityResolutionError. Include required payload fields (provider, operation, requested_mode, requested_environment, key_scope, supported_modes, supported_environments, suggested_resolution).

    ', status: todo}
- {id: p2-adapter-guardrails, content: '- [ ] [AGENT] P2. Add standardized preflight capability checks in all interface adapters before network calls. Guardrail checks must run before HTTP/WS call. Reject unsupported mode/env/auth combinations with explicit error payload.

    ', status: todo}
- {id: p3-mapping-unification, content: '- [ ] [AGENT] P3. Normalize all adapters to one raw->validate->canonical pipeline using UAC schemas. Flow: resolve capability record -> validate mode/env/auth -> resolve endpoint -> execute call -> validate raw payload -> map to canonical -> return.

    ', status: todo}
- {id: p3-duplicate-mapping-elimination, content: '- [ ] [AGENT] P3. Detect and remove duplicate raw->canonical mapping logic across interfaces. Extract shared normalizers where repeated. Single code path only.

    ', status: todo}
- {id: p4-service-adoption, content: '- [ ] [AGENT] P4. Refactor services to consume canonical outputs only. Remove direct raw/provider parsing paths. Services call interfaces/domain client; capability resolution determines if call is legal.

    ', status: todo}
- {id: p5-feature-interface-contract, content: '- [ ] [AGENT] P5. Define or formalize feature interface contract layer used by services for alternative data/features. Include capability metadata for feature providers and mode support. Align unified-feature-calculator-library.

    ', status: todo}
- {id: p6-import-surface-enforcement, content: '- [ ] [AGENT] P6. Enforce public import policy (top-level/first-level namespaces). Block non-public deep imports. Document preferred: from unified_api_contracts import <stable public symbols>; from unified_api_contracts.schemas import <schema symbols>.

    ', status: todo}
- {id: p7-test-matrix, content: '- [ ] [AGENT] P7. Build matrix tests for mode/env/auth compatibility across all interfaces and major providers. Cover UnsupportedModeError, UnsupportedEnvironmentError, ApiKeyScopeMismatchError scenarios.

    ', status: todo}
- {id: p7-vcr-alignment, content: '- [ ] [AGENT] P7. Ensure VCR replay validates both raw schema conformance and canonical output invariants. Update cassette tests to assert capability metadata.

    ', status: todo}
- {id: p8-codex-ssot, content: '- [ ] [AGENT] P8. Publish SSOT docs in unified-trading-codex: ownership matrix, flow diagram, capability taxonomy, error taxonomy, migration guide.

    ', status: todo}
- {id: p8-quality-gate-validators, content: '- [ ] [AGENT] P8. Add validators for capability coverage, unsupported-combo guardrails, and duplicate mapping detection. Integrate into quality-gates-base scripts.

    ', status: todo}
isProject: false
---

# Interfaces Capability Contract Unification

Unify architecture, import policy, capability registry, and runtime guardrails across all interface repos and their
consuming services.

---

## Architecture Contract

### Ownership

| Owner               | Owns                                                                                                                                                                    | Boundary                                        |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| **UAC**             | External raw schemas, canonical normalized schemas, provider capability metadata registry, endpoint metadata (env/mode/domain/auth scope), public import/export surface | —                                               |
| **Interface repos** | Runtime IO/adapters, raw schema validation invocation, mapping execution raw->canonical, capability checks before call execution                                        | —                                               |
| **UIC**             | Internal cross-service contracts/events/domain records                                                                                                                  | No ownership of external provider raw schemas   |
| **Services**        | Orchestration and business logic                                                                                                                                        | Do not implement provider-specific raw mappings |

### Interface Catalog

| Repo                               | Domain                                     |
| ---------------------------------- | ------------------------------------------ |
| unified-market-interface           | tradfi/cefi/alt-data market feeds          |
| unified-reference-data-interface   | instruments/reference/master data          |
| unified-trade-execution-interface  | order/execution routing                    |
| unified-sports-execution-interface | sportsbook/exchange execution              |
| unified-defi-execution-interface   | protocol interactions (Aave, Morpho, etc.) |
| unified-position-interface         | positions/balances/exposure                |
| unified-feature-calculator-library | standardized feature contract surfaces     |

---

## Capability Registry Model

- **SSOT repo:** unified-api-contracts
- **Scope:** provider + endpoint + operation
- **Guarantees:**
  - Interface adapter can resolve endpoint deterministically from mode+env+provider
  - Adapter can reject unsupported combinations before network call

---

## Runtime Guardrails

- Guardrail checks happen **before** HTTP/WS call
- Errors are explicit, non-silent, and user-actionable
- Error payload must include: provider, operation, requested_mode, requested_environment, key_scope, supported_modes,
  supported_environments, suggested_resolution

---

## Standard Execution Flow

1. Resolve capability record from UAC registry
2. Validate requested mode/env/auth against capability
3. Resolve endpoint from capability metadata
4. Execute API call in interface adapter
5. Validate raw payload against UAC raw schema
6. Map raw payload to UAC canonical schema
7. Return canonical object to caller/service

---

## Acceptance Criteria

- [ ] Every interface resolves provider endpoint via UAC capability metadata (no ad-hoc literals for core paths)
- [ ] Every interface rejects unsupported mode/env/auth combinations pre-call with explicit error payload
- [ ] Every adapter pipeline uses raw validation + canonical output
- [ ] Services no longer implement provider-specific raw parsing
- [ ] Public import paths are documented and enforced
- [ ] Capability registry coverage reaches all active providers and operations used in production paths

---

## Non-Goals

- Backward-compatibility shims for legacy deep imports
- Dual old/new mapping paths retained after migration
- Service-level schema ownership that belongs in UAC/UIC
