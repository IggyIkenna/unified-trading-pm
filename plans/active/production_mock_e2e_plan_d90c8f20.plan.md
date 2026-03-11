---
name: Production Mock E2E Plan
overview:
  "Bring all 60+ repos to production-standard mock E2E testability: libraries via UAC/UIC validation and VCR cassettes;
  services and APIs via mock data replay, error handling, events, and load/performance checks; UIs via mock API, smoke
  tests, and demo mode. Mock-only default in CI; optional sandbox mode when secrets present."
todos:
  - id: phase1-vcr-consolidate
    content:
      Consolidate VCR cassettes into UAC; migrate unified-defi-execution-interface and execution-service cassettes
    status: pending
  - id: phase1-orphan-check
    content: Add cassette orphan check to quality gates or codex (no orphan cassettes, no orphan tests)
    status: pending
  - id: phase1-interface-vcr
    content: Ensure all 7 external interfaces have VCR tests and cassettes in UAC
    status: pending
  - id: phase2-service-mock-replay
    content: Add mock data replay E2E/integration tests for all services (live + batch)
    status: pending
  - id: phase2-error-events
    content: Add error handling and event propagation tests per service
    status: pending
  - id: phase2-load-memory
    content: Add load and memory behavior tests where applicable
    status: pending
  - id: phase3-api-integration
    content: Add tests/integration/ and domain data mocking for all API repos
    status: pending
  - id: phase4-ui-smoke
    content: Add smoke tests for every major UI route and feature with VITE_MOCK_API
    status: pending
  - id: phase4-ui-websocket
    content: Add WebSocket mock and edge-case scenarios for UIs
    status: pending
  - id: phase5-sandbox-mode
    content: Define CLOUD_SANDBOX_MODE and VITE_SANDBOX_MODE; optional CI job when secrets present
    status: pending
  - id: phase5-extreme-fixtures
    content: Create extreme load and market move fixtures; wire into services and UIs
    status: pending
  - id: phase6-rollout
    content: Rollout across all 60+ repos; create per-repo checklist from manifest
    status: pending
isProject: false
---

# Production-Standard Mock E2E for All Repos

## Current State (from audit + explore)

| Area              | Status                                                                    | Gap                                                                                                   |
| ----------------- | ------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| **VCR cassettes** | UAC has `unified_api_contracts_external/<venue>/mocks/`; 46 cassette dirs | `unified-defi-execution-interface`, `execution-service` use per-repo `tests/cassettes/` — not aligned |
| **Libraries**     | Integration tests in 7+ interface repos; UAC/UIC alignment tests          | Orphan cassette check; vcrpy vs manual YAML; cassette placement rule enforcement                      |
| **Services**      | `tests/integration/` in many; CLOUD_MOCK_MODE in base scripts             | API-level mock replay; error/event/load/memory checks; batch vs live symmetry                         |
| **APIs**          | Some conftest fixtures                                                    | Often lack `tests/integration/`; domain data mocking                                                  |
| **UIs**           | `mock-api.ts` + `VITE_MOCK_API` per UI                                    | No shared mock package; smoke coverage gaps; WebSocket mock; demo mode                                |
| **Sandbox**       | Not formalized                                                            | No `CLOUD_SANDBOX_MODE` / `VITE_SANDBOX_MODE` for optional live-like runs                             |

---

## Phase 1: Libraries — UAC/UIC + VCR Consolidation

**Goal:** Libraries are production-ready when UAC/UIC validated and every external schema has a VCR cassette with no
orphans.

### 1.1 VCR Cassette SSOT

- **Canonical location:**
  `unified-api-contracts/unified_api_contracts/unified_api_contracts_external/<venue>/mocks/<endpoint>.yaml`
- **Migration:** Move per-repo cassettes from `unified-defi-execution-interface/tests/cassettes/` and
  `execution-service/tests/cassettes/` into UAC under the correct venue paths. Update tests to load from UAC path (or
  via a shared helper).
- **Orphan check:** Add a quality-gate step (or codex check) that fails if any cassette in UAC has no corresponding test
  that replays it, and if any test references a cassette that does not exist.
- **vcrpy vs manual:** Standardize on vcrpy for recording/replay where possible; document manual YAML loading as
  fallback for non-HTTP flows.

### 1.2 External Interfaces (7 repos)

Per [trading_system_audit_prompt.plan.md](unified-trading-pm/plans/active/trading_system_audit_prompt.plan.md) Section
10:

- `unified-market-interface`, `unified-trade-execution-interface`, `unified-reference-data-interface`,
  `unified-position-interface`, `unified-sports-execution-interface`, `unified-defi-execution-interface`,
  `unified-cloud-interface`
- Each must have VCR-recorded integration tests validating schemas from UAC.
- Cassettes in `unified_api_contracts_external/<venue>/mocks/`.
- All integration tests run with mocked deps (no live cloud in quickmerge).

### 1.3 UIC as SSOT

- UIC schemas are internal SSOT; no separate “validation” beyond contract alignment tests.
- Ensure `test_contract_alignment.py` and `test_ac_uic_alignment.py` (or equivalent) pass in UAC/UIC and dependent
  repos.
- Libraries with private deps: `tests/integration/` with Layer 1.5 mock integration tests per dep boundary.

---

## Phase 2: Services — Mock Replay, Errors, Events, Load, Memory

**Goal:** Services are E2E-testable with mock data in live and batch mode; error handling, event propagation, and
resource behavior validated.

### 2.1 Mock Data Replay

- Each service has `tests/e2e/` or `tests/integration/` scenarios that:
  - Start the service (or its engine) with `CLOUD_MOCK_MODE=true`.
  - Replay mock data from fixtures (aligned with UAC/UIC schemas).
  - Exercise live and batch code paths where applicable.
- Use existing patterns: `tests/fixtures/`, `tests/conftest.py`, `tests/mocks.py` (e.g.
  [deployment-service](deployment-service/tests/mocks.py)).

### 2.2 Error and Config Handling

- Tests for: missing upstream data, missing optional config, partial failures.
- Fail-fast behavior per [hardening-standards.mdc](.cursor/rules/standards/hardening-standards.mdc).
- Add or extend `test_error_handling.py` / `test_config_handling.py` per service.

### 2.3 Event Propagation

- Per [observability-compliance.mdc](.cursor/rules/misc/observability-compliance.mdc): `AUTH_FAILURE`,
  `SECRET_ACCESSED`, `CONFIG_CHANGED`, etc.
- Add `test_event_logging.py` where missing (audit notes 46 repos already have it).
- Assert required events are emitted for key flows.

### 2.4 Load and Performance

- Rate limiting: validate at interface/adapter level (e.g. circuit breaker, backoff).
- Memory: tests that exercise high-volume or long-running flows with mock data; assert no unbounded growth (or document
  expected bounds).
- Use `pytest-benchmark` or similar for regression detection where appropriate.

### 2.5 API-Level Testing

- Services that expose HTTP: smoke tests against `/health`, `/readiness`, and key domain endpoints with mock data.
- Reuse `system-integration-tests` patterns for Layer 3a smoke.

---

## Phase 3: APIs — Same as Services + Domain Data

**Goal:** APIs have the same guarantees as services, plus domain data mocking.

### 3.1 Integration Tests

- Add `tests/integration/` where missing (e.g. [client-reporting-api](client-reporting-api) has conftest but not full
  integration layout).
- One test file per private dependency boundary.

### 3.2 Domain Data Mocking

- Mock service responses (e.g. market-data-api, execution-results-api) for API repos that depend on them.
- Use VCR-style fixtures or in-memory mocks so APIs can run E2E without live services.

### 3.3 Smoke Tests

- `/health`, `/readiness`, and critical GET/POST endpoints with mock payloads.

---

## Phase 4: UIs — Mock API, Smoke, Edge Cases, Demo Mode

**Goal:** UIs are demo- and test-ready with mock data; every screen and flow has smoke coverage; edge cases and
WebSockets covered.

### 4.1 Shared Mock API (Optional)

- Evaluate `@unified-trading/ui-kit` or a new `unified-mock-api` package for shared mock handlers and data shapes.
- Current: each UI has `src/lib/mock-api.ts`; consolidate where it reduces duplication without over-engineering.

### 4.2 Smoke Tests

- Vitest/Playwright: smoke test for every major route and feature.
- Use `VITE_MOCK_API=true` so no real backend required.
- Cover: navigation, forms, tables, charts, error states.

### 4.3 Edge Cases and WebSockets

- Mock WebSocket streams with synthetic data (e.g. random ticks, extreme moves).
- Test: empty states, loading states, error states, large datasets.
- Scenarios: extreme loads, flash crashes, missing instruments.

### 4.4 Demo Mode

- `VITE_MOCK_API=true` as default for local dev and CI.
- Document how to run UIs in “demo mode” for stakeholders.

---

## Phase 5: Sandbox and Extreme Scenarios

**Goal:** Optional sandbox mode for CI when secrets present; synthetic extreme scenarios for load and market moves.

### 5.1 Sandbox Mode

- **Env vars:** `CLOUD_SANDBOX_MODE`, `VITE_SANDBOX_MODE` (or equivalent).
- **Behavior:** When set and sandbox/UAT API keys are available, tests can call real sandbox endpoints.
- **CI:** Default remains mock-only; add optional job or flag (e.g. `--sandbox`) to run sandbox tests when secrets
  exist.
- **Docs:** Document in [dev-environment-vars.md](unified-trading-pm/docs/dev-environment-vars.md).

### 5.2 Extreme Scenarios

- Fixtures for: high message volume, extreme price moves, missing instruments, partial failures.
- Replay these in services and UIs to validate stability and UX under stress.

---

## Phase 6: Quality Gates and Rollout

### 6.1 Quality Gate Updates

- Add cassette orphan check to UAC (or codex step).
- Add `tests/integration/` presence check for services and APIs (or extend existing).
- Ensure `CLOUD_MOCK_MODE=true` in all Python repo workflows (per
  [mft_audit_full_remediation_2026_03_11.plan.md](unified-trading-pm/plans/active/mft_audit_full_remediation_2026_03_11.plan.md)).
- UI repos: ensure `VITE_MOCK_API` is set in CI for test runs.

### 6.2 Rollout Order

1. **Libraries** (T0/T1): UAC, UIC, interfaces — cassette consolidation, orphan check.
2. **Services** (T2/T3): mock replay, error/event/load tests.
3. **APIs**: integration tests, domain mocks, smoke.
4. **UIs**: smoke, edge cases, WebSocket mocks, demo mode.
5. **Sandbox + extreme**: optional modes and fixtures.

### 6.3 Repo Inventory

- Use `workspace-manifest.json` to enumerate repos by `type` and `arch_tier`.
- Create checklist per repo: VCR, integration tests, mock replay, events, load, smoke, sandbox.

---

## Key Files and References

| Reference                                                                                                  | Purpose                                       |
| ---------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| [trading_system_audit_prompt.plan.md](unified-trading-pm/plans/active/trading_system_audit_prompt.plan.md) | Audit Sections 10 (integration), 14 (orphans) |
| [integration-testing-layers.mdc](.cursor/rules/testing/integration-testing-layers.mdc)                     | 5-layer strategy; cassette placement          |
| [CI-CD-FLOW.md](unified-trading-pm/docs/repo-management/CI-CD-FLOW.md)                                     | run-all-quality-gates, CLOUD_MOCK_MODE        |
| [observability-compliance.mdc](.cursor/rules/misc/observability-compliance.mdc)                            | Event requirements                            |
| `unified_api_contracts_external/<venue>/mocks/`                                                            | Canonical cassette location                   |

---

## Mermaid: Test Mode Flow

```mermaid
flowchart TB
    subgraph CI [CI Quality Gates]
        MockOnly[CLOUD_MOCK_MODE=true]
        MockOnly --> QG[Quality Gates]
    end

    subgraph Optional [Optional Sandbox]
        Sandbox[CLOUD_SANDBOX_MODE + keys]
        Sandbox --> SandboxQG[Sandbox E2E]
    end

    subgraph Local [Local / Demo]
        ViteMock[VITE_MOCK_API=true]
        ViteMock --> UIDemo[UI Demo Mode]
    end

    QG --> Pass[PASS]
    SandboxQG --> Pass
    UIDemo --> Demo[Demo Ready]
```

---

## Success Criteria

- **Libraries:** UAC/UIC alignment pass; every external schema has a cassette; zero cassette orphans.
- **Services/APIs:** Integration tests per dep boundary; mock replay in live and batch; error/event/load tests; smoke on
  key endpoints.
- **UIs:** Smoke tests for all major flows; mock API and WebSocket; demo mode works.
- **Sandbox:** Optional CI mode when secrets present; documented.
- **Extreme:** Fixtures and scenarios for load and market stress; replayable in tests.
