---
doc_type: plan
title: unified-api-contracts full audit
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-03'
overview: Full audit of unified-api-contracts and unified-internal-contracts with a combined split—AC = external + normalised only, UIC = internal only; AC must not depend on UIC; canonical namings needed by AC stay in AC.
todos: []
isProject: false
---

# Combined Audit: unified-api-contracts + unified-internal-contracts

## AC/UIC Refactor — Layout Status & QG Blockers

**Plans:** [ac_package_layout_refactor_45f5eb10.md](ac_package_layout_refactor_45f5eb10.md)

| Phase                                    | Status                                                                                                      |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Phase 0 (SSOT + cursor rules)            | Done                                                                                                        |
| Phases 1–8 (package layout)              | Done — venue_manifest, sports, fix, nautilus, regulatory, prime_broker under unified_api_contracts_external |
| Phase 9 (root, tests, QG, 2-min timeout) | **QG fails:** 63 lint errors (E501 line length, F401 unused imports)                                        |
| Phase 10 (workspace consumers)           | Blocked by Phase 9                                                                                          |

**QG lint blockers:** Run `ruff check --fix` and manually fix E501 (line length) in AC. Ensure
`pytest -m "not integration"` completes in <2 min. Workspace consumers: update imports after AC QG passes.

**Does not block first deployment:** AC/UIC refactor improves structure; existing imports work via top-level re-exports.

---

## Intended split (design rule)

- **unified-api-contracts (AC):** Everything **external** to our private repos (needs API key / external connection) + a
  **normalised** layer (one-hop from raw external responses). No purely internal service-to-service contracts.
- **unified-internal-contracts (UIC):** Purely **internal** contracts between private components (no API key, not
  normalised-from-external, not "getting something external").
- **Dependency rule:** AC must **not** depend on UIC (AC is Tier 0). Canonical namings that AC needs for
  external/normalised (e.g. venue enums, error classification at API boundary) stay in AC.

- **VCR and live schema validation:** Done in the **interfaces** that depend on AC (interfaces hold API keys). AC holds
  only schemas and static examples. Interfaces that perform VCR and contract-vs-reality validation:
  **unified-trade-execution-interface**, **unified-sports-execution-interface**, **unified-reference-data-interface**,
  **unified-position-interface**, **unified-market-interface**, **unified-cloud-interface**.

---

# Part A: unified-api-contracts (AC) — existing audit

(See full plan in .cursor/plans/ for sections 1–8: layout, docs, .cursor/ boundary, deprecated files, file size, import
standards, other alignment, summary table and suggested order.)

---

# Part B: unified-internal-contracts (UIC) — audit

**Role:** SSOT for internal message schemas, topic names, and request/response/error contracts (no external APIs, no API
keys).

**Current content (correct for "internal only"):** events, market_data, positions, pubsub, risk, features, ml, schemas,
reference, messaging, defi, execution (ManualInstruction).

**Dependencies:** Only pydantic; no dependency on AC. Tier 0. OK.

**Alignment tests:** test_uic_ac_alignment.py imports from unified_api_contracts.internal.\*; obsolete once AC.internal
is removed.

**schema_registry.json:** Remove entries for unified_api_contracts.internal.\* when AC.internal is deleted.

**Verdict:** UIC is already internal-only and well-scoped.

**Before deleting AC internal/:** Verify every AC internal symbol (config, domain, execution, health, signals, sor) has
an equivalent in UIC; add any gaps to UIC first, then delete AC internal/.

---

# Part C: Combined split and remediation

**What belongs where:** External + FIX + nautilus + normalised + canonical namings → AC. Events, pubsub, risk, features,
ml, config, health, execution, signals, sor → UIC only (delete from AC). internal_execution_services, prime_broker,
regulatory, shared → classify (internal → UIC/delete; external → AC).

**Dependency:** AC must NOT depend on UIC. UIC may optionally depend on AC to re-export normalised types.

**Normalised in AC:** Make unified_normalised_contracts self-contained (Option A: own definitions in AC; Option B: UIC
depends on AC and re-exports).

**VCR / live capture:** Move collected_responses/ and generated_schemas/ responsibility to the six interfaces
(integration tests). Remove or relocate from AC: collect_responses.py, capture_api_responses.py, validate_schemas.py
(live/--generate-schemas), verify_contracts_vs_reality\*.py. AC keeps only schemas and static examples.

**Docs and SSOT updates:** (1) Codex 00-SSOT-INDEX.md — AC = contracts only; VCR/live validation in the six interfaces;
add internal contracts row. (2) Codex 05-infrastructure/contracts-integration.md — same. (3) Codex 02-data (VCR/schema
ownership) — interfaces record/validate; AC holds schemas and examples. (4) Cursor rules: vcr-ownership.mdc (interfaces
do VCR; list six), unified-api-contracts-usage.mdc (live verification in interfaces), contracts-integration.mdc (one
line on six interfaces). (5) AC README/docs — point live validation to interfaces.

**Orphaned-schemas audit (two types):** (1) **Not normalised** — external/venue schemas that have no corresponding
normalised form in AC. (2) **Not used by any interface** — schemas that none of the six interfaces import or use. Single
report, two sections; list by module and symbol; output in unified-trading-pm/docs/audit/ or AC docs.

**Combined remediation order:** (1) AC docs + script move + .bak + gitignore; (2) normalised self-contained in AC; (3)
verify UIC has all AC internal symbols, then remove internal (and classify other dirs) from AC, update AC tests; (4)
UIC: remove alignment tests and schema_registry AC.internal entries; (5) confirm no production imports of AC.internal;
(6) move VCR/live scripts to interfaces, remove collected_responses/generated_schemas from AC; (7) update docs and SSOT
as above; (8) **produce orphaned-schemas audit report** — Type 1: not normalised; Type 2: not used by any of the six
interfaces; (9) optional AC layout + remove sys.modules alias.
