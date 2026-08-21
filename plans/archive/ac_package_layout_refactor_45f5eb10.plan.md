---
doc_type: plan
title: AC refactor and SSOT consolidation
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-03"
overview:
  "(1) Add codex as SSOT for AC vs UIC scope, dependency rule, and layout (with cursor rules routing to codex). (2)
  Refactor unified-api-contracts so top-level packages live under shared, unified_api_contracts_external, or move to
  UIC. Success: abidance by new rules/structure, AC quality gates pass, unit tests (schema validation, normalisation,
  mapping) finish in under 2 minutes. Integration tests are NOT run in AC — interfaces invoke them (they have
  connectivity and API keys)."
todos:
  - {
      id: phase0,
      content:
        "SSOT and cursor rules (codex doc, SSOT-INDEX, contracts-integration, vcr-cassette-ownership, AC ARCHITECTURE,
        cursor rules)",
      status: completed,
    }
  - { id: phase1-8, content: Package layout refactor agents 1-8 (parallel), status: in_progress }
  - { id: phase9, content: "Root and cross-refs, AC quality gates, test timeout", status: pending }
  - { id: phase10, content: Workspace consumers import updates, status: pending }
isProject: false
---

# Master Plan: AC Package Layout Refactor + SSOT Consolidation

## Success criteria

- **Abidance:** New rules and structure enforced; AC has no imports from unified-internal-contracts; mapping schemas
  remain in AC.
- **Quality gates:** unified-api-contracts passes `bash scripts/quality-gates.sh --no-fix` (or equivalent).
- **Tests:** Unit tests only — external contracts → normalisation schema validation, mapping, coverage. **No integration
  tests** (VCR replay, live validation) — those are invoked by the interfaces (UMI, UTEI, etc.), which have connectivity
  and API keys.
- **Test duration:** All AC tests finish within **2 minutes**.

---

## Phase 0: SSOT and cursor rules (run first)

Establish codex as SSOT for constraints; cursor rules route to codex. Can run as one agent or split.

### 0.1 Create codex SSOT doc

Create
[unified-trading-/codex/02-data/contracts-scope-and-layout.md](unified-trading-/codex/02-data/contracts-scope-and-layout.md):

- **Dependency rule:** unified-api-contracts must not import from unified-internal-contracts. AC is Tier 0 leaf; mapping
  schemas (canonical IDs, venue manifest, normalised types) stay in AC.
- **Scope rule:** AC = external API contracts + mapping surface; UIC = internal-only.
- **Layout rule:** Three buckets — shared, unified_api_contracts_external, unified_normalised_contracts.
- Add: "For full detail: unified-api-contracts/docs/PACKAGE_LAYOUT_AND_SCOPE.md. VCR:
  02-data/vcr-cassette-ownership.md."

### 0.2 Update codex and AC docs

- **SSOT-INDEX:** "External API schemas — layout & placement rule" → `02-data/contracts-scope-and-layout.md`; "Internal
  contracts" → add scope ref to same.
- **contracts-integration.md:** Add constraints SSOT ref; update placement rule to point to codex.
- **vcr-cassette-ownership.md:** Add cross-ref to contracts-scope-and-layout.md in Circular Dependency Rules.
- **AC ARCHITECTURE.md:** Add SSOT ref to codex and PACKAGE_LAYOUT_AND_SCOPE.md.

### 0.3 Update cursor rules

- **contracts-integration.mdc:** CODEX: add 02-data/contracts-scope-and-layout.md.
- **unified-api-contracts-usage.mdc:** Change "Full specification" to codex (fix broken
  06-coding-standards/unified-api-contracts.md ref).
- **dag-enforcement.mdc:** Add "AC cannot import UIC: 02-data/contracts-scope-and-layout.md."

---

## Phase 1–8: Package layout refactor (parallel agents)

Constraints from [PACKAGE_LAYOUT_AND_SCOPE.md](unified-api-contracts/docs/PACKAGE_LAYOUT_AND_SCOPE.md): AC cannot import
UIC; mapping schemas stay in AC; three buckets.

| Agent | Scope                | Deliverable                                                                                                           |
| ----- | -------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **1** | venue_manifest       | Move to `unified_api_contracts_external/venue_manifest/`. Update internal imports.                                    |
| **2** | sports               | Move to `unified_api_contracts_external/sports/`. Update internal imports.                                            |
| **3** | nautilus             | Move to `unified_api_contracts_external/nautilus/`. Update internal imports.                                          |
| **4** | fix                  | Move to `unified_api_contracts_external/fix/`. Update internal imports.                                               |
| **5** | regulatory           | Move to `unified_api_contracts_external/regulatory/`. Update internal imports.                                        |
| **6** | prime_broker         | Move to `unified_api_contracts_external/prime_broker/`. Update internal imports.                                      |
| **7** | schemas split        | Move cross-venue content to shared; re-export from schemas; resolve ErrorAction duplicate; leave risk.py for Agent 8. |
| **8** | Move internal to UIC | Add risk module to unified-internal-contracts; remove schemas/risk.py from AC; ensure no AC→UIC imports.              |

---

## Phase 9: Root, tests, quality gates, test timeout (after 1–7)

- Update [unified_api_contracts/**init**.py](unified-api-contracts/unified_api_contracts/__init__.py) to import from new
  paths; preserve top-level re-exports.
- Update venue_manifest/internal_services refs to external.fix.
- Update all AC tests to new import paths.
- Update defi/schemas.py to new schemas/shared path.
- **Ensure AC quality gates run only unit tests** (exclude integration): Run `pytest tests/ -m "not integration"` so
  root tests (test_normalization, test_contract_alignment, test_schema_validation, test_contracts_vs_reality,
  test_venue_contract_coverage, etc.) and tests/unit/ are included, while VCR tests (test_vcr_replay.py, tests/vcr/) are
  excluded. If quality-gates.sh currently runs only tests/unit/, update it to run `tests/ -m "not integration"` for AC
  so schema validation and mapping tests at root are covered.
- **Test timeout:** Ensure AC test run finishes in under 2 minutes. Use `--timeout=120` or equivalent; keep Hypothesis
  max_examples low (default profile); run only unit tests.
- Run quality gates in AC; fix any remaining errors.

---

## Phase 10: Workspace consumers (after Phase 9)

- Grep workspace for `from unified_api_contracts.(sports|venue_manifest|schemas|nautilus|fix|regulatory|prime_broker)`.
- Update each consumer repo to new import paths (or rely on preserved top-level re-exports).
- Run quality gates in each touched repo.

---

## Execution order

1. **Phase 0** (SSOT + cursor rules) — run first.
2. **Phase 1–8** (parallel).
3. **Phase 9** (root, tests, QG, timeout) — after 1–7.
4. **Phase 10** (workspace consumers) — after Phase 9.

---

## Test scope (AC only)

| Run in AC                                                      | Do not run in AC                            |
| -------------------------------------------------------------- | ------------------------------------------- |
| Schema validation (examples/\*.json, Pydantic)                 | VCR replay (test_vcr_replay.py, tests/vcr/) |
| Normalisation (BinanceTrade→CanonicalTrade, etc.)              | Live API validation                         |
| Mapping tests (venue manifest, coverage)                       | Integration tests requiring API keys        |
| Unit tests (test_contract_alignment, test_normalization, etc.) |                                             |

Interfaces (UMI, UTEI, etc.) invoke VCR and live validation; they have connectivity and API keys.

---

## Verification checklist

- Codex 02-data/contracts-scope-and-layout.md exists; SSOT-INDEX and cursor rules reference it.
- AC: `timeout 120 basedpyright unified_api_contracts/` passes; no `unified_internal_contracts` imports.
- AC: `pytest -m "not integration"` (or tests/unit/ only) passes; run completes in under 2 minutes.
- AC: `bash scripts/quality-gates.sh --no-fix` passes.
- UIC: risk module importable; tests pass.
- Workspace consumers: quality gates pass after import updates.
