---
doc_type: plan
title: Schema Contracts Full Audit
summary: 'Comprehensive audit of all schema/model definitions across all 60+ repos. Enforces that every schema lives in
  unified-api-contracts (external API) or unified-internal-contracts (internal/domain), with no exceptions. Produces a violation
  catalogue covering: misplaced schemas, duplicates, conflicts, orphaned schemas, and tier boundary issues. Feeds Plans
  #11 (orphan utilization) and #11b (UAC normalization). Outputs: audit document + codex/cursor rules updates. Remediation
  plan follows separately.'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [alerting-service, client-reporting-api, deployment-api, deployment-service, execution-service, instruments-service]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-06"
todos:
  - {
      id: agent1-contract-repos,
      content:
        "Agent 1: Deep inventory of UAC and UIC — all schema definitions, UAC/UIC duplicates, orphaned schemas in both,
        existing UIC→UAC import boundary.",
      status: completed,
    }
  - {
      id: agent2-t0-libs,
      content:
        "Agent 2: T0 libs (UEI, UCI-cloud, execution-algo, matching-engine) — find schemas that should be in UIC; verify
        no forbidden UAC/UIC imports.",
      status: completed,
    }
  - {
      id: agent3-t1-libs,
      content:
        "Agent 3: T1 libs (URDI, config-interface, trading-library) — classify schemas, check cross-import graph,
        identify MISPLACE-UIC candidates.",
      status: completed,
    }
  - {
      id: agent4-t2-market-exec,
      content:
        "Agent 4: T2 libs (market-interface, trade-execution-interface) — all adapter Pydantic models → MISPLACE-UAC;
        check for duplicates already in UAC.",
      status: completed,
    }
  - {
      id: agent5-t2-t3-rest,
      content:
        "Agent 5: T2/T3 libs (ml-interface, feature-calc-lib, position-interface, defi-exec, sports-exec, domain-client)
        — same as Agent 4; check InstrumentKey cross-import scope.",
      status: completed,
    }
  - {
      id: agent6-services-a,
      content:
        "Agent 6: Services A (execution-service, strategy-service, strategy-validation-service,
        risk-and-exposure-service, alerting-service) — all schemas are now MISPLACE-UIC; document target UIC
        subdirectory per schema.",
      status: completed,
    }
  - {
      id: agent7-services-b,
      content:
        "Agent 7: Services B (market-data-processing-service, market-tick-data-service, market-data-api,
        instruments-service, features-calendar-service).",
      status: completed,
    }
  - {
      id: agent8-services-c,
      content:
        "Agent 8: Services C (features-delta-one, features-volatility, features-cross-instrument,
        features-multi-timeframe, features-onchain, features-sports-service).",
      status: completed,
    }
  - {
      id: agent9-services-d,
      content:
        "Agent 9: Services D + APIs (ml-inference, ml-training, pnl-attribution, position-balance-monitor,
        execution-results-api, client-reporting-api, deployment-api, deployment-service).",
      status: completed,
    }
  - {
      id: agent10-codex-rules,
      content:
        "Agent 10: Codex + cursor rules audit — all existing schema placement rules; gaps vs master rules;
        schema-governance.md service-owned pattern to be retired; produce diff of needed changes.",
      status: completed,
    }
  - {
      id: compile-audit-doc,
      content: Compile all agent findings into unified-trading-pm/plans/archive/SCHEMA_CONTRACTS_AUDIT.md.,
      status: completed,
    }
  - {
      id: update-codex-cursor-rules,
      content:
        "Update codex docs and cursor rules based on audit findings (new .mdc rules + updates to
        contracts-scope-and-layout.md, TIER-ARCHITECTURE.md, schema-governance.md).",
      status: completed,
    }
isProject: true
---

# Schema Contracts Full Audit

**Status:** Active **Created:** 2026-03-05 **Phase:** 0c (runs alongside Phase 0 standards enforcement) **Feeds:** Plan
#11 (orphan-contracts-utilization) · Plan #11b (uac_schema_normalization_complete) **Supersedes (partially):** AC/UIC
section of Plan #25 (trading_system_audit_prompt)

---

## Context

The architectural intent is that every schema in the codebase must live in one of exactly two authoritative contract
repos:

- **unified-api-contracts (UAC)** — external API-facing schemas: raw venue request/response models, normalization
  schemas, and canonical types that are the _output_ of normalization.
- **unified-internal-contracts (UIC)** — internal cross-repo contracts: canonical types used in messaging/pub-sub, event
  envelopes, error records, shared identifiers, service domain data schemas, and anything cross-imported by two or more
  repos.

**No exceptions.** Service domain data schemas (`schemas/output_schemas.py`) must move to UIC. Services access schemas
via `unified-trading-library` or `unified-domain-client`. This ensures any service can find another service's data shape
in UIC without importing that service (which would violate the tier DAG).

**Known pre-audit violations (confirmed):**

- `InstrumentRecord` defined in both UAC (`unified_normalised_contracts/domain.py`) and UIC (`reference/instrument.py`)
  — DUPLICATE
- `CanonicalOraclePrice`, `CanonicalStakingRate`, `CanonicalOptionsChainEntry` defined in both repos — DUPLICATE
- UIC `market_data/__init__.py` imports from UAC (canonical re-exports) — correct direction but not formalized in tier
  model
- Adapter Pydantic models (`_deribit_models.py`, `_defi_graph_models.py`) in `unified-market-interface` — MISPLACE-UAC
- Test file `test_ac_uic_alignment.py` in UAC imports UIC — CIRCULAR (UAC is T0 leaf, must not import UIC even in tests)
- 23+ service repos define local domain schemas — MISPLACE-UIC

---

## Master Schema Placement Rules

| Category                                               | Where It Lives                                          | Rationale                                                    |
| ------------------------------------------------------ | ------------------------------------------------------- | ------------------------------------------------------------ |
| Raw venue API request/response models                  | UAC `unified_api_contracts_external/<venue>/schemas.py` | External API shapes; UAC is normalization SSOT               |
| Adapter-private Pydantic models (`_<venue>_models.py`) | UAC `unified_api_contracts_external/<venue>/schemas.py` | They parse external API responses — same rule, no exceptions |
| Normalization schemas (map raw → canonical)            | UAC `unified_api_contracts/schemas/`                    | Normalization layer                                          |
| Canonical types output by normalization                | UAC `unified_normalised_contracts/`                     | Normalization output = external-derived canonical            |
| Canonical types used in internal messaging/pub-sub     | UIC (relevant domain subdirectory)                      | Messaging contracts                                          |
| Event envelopes (lifecycle, domain publish events)     | UIC `events.py` / `pubsub.py`                           | Internal messaging                                           |
| Shared identifiers cross-imported by 2+ repos          | UIC `reference/`                                        | Cross-repo contract                                          |
| Error records for cross-repo error handling            | UIC `schemas/errors.py`                                 | Internal contract                                            |
| Service domain data schema (primary output shape)      | UIC `domain/<service-name>/`                            | All schemas in UIC; accessed via UTL/UDC                     |
| Service-to-library protocol routing                    | Library tier (UTL, UCI, etc.)                           | Library owns protocol; schema lives in UIC                   |
| Interface-public types cross-imported elsewhere        | UIC                                                     | Determined by actual import graph                            |
| Interface-internal types not cross-imported            | Interface (stays)                                       | Not a cross-repo contract                                    |

**UIC→UAC dependency rule:** UIC may import from UAC (normalization canonicals re-exported for messaging use). UAC must
NOT import from UIC — not even in tests. Formalization required: UAC = true T0 leaf; UIC = T0-with-UAC-dependency. Build
order must place UAC before UIC.

---

## Classification Taxonomy

| Code            | Meaning                                                                                       |
| --------------- | --------------------------------------------------------------------------------------------- |
| `CORRECT-UAC`   | External API schema, correctly in UAC                                                         |
| `CORRECT-UIC`   | Internal/domain contract, correctly in UIC                                                    |
| `CORRECT-LOCAL` | Interface-internal type, not cross-imported — acceptable                                      |
| `MISPLACE-UAC`  | Should move to UAC (adapter model, venue API parser)                                          |
| `MISPLACE-UIC`  | Should move to UIC (cross-imported, cross-repo, or domain data schema in a service/interface) |
| `DUPLICATE`     | Same concept defined in 2+ places (note all locations + field diff)                           |
| `CONFLICT`      | Same name, incompatible definitions in different repos                                        |
| `ORPHAN`        | Defined in UAC or UIC, never imported anywhere in codebase                                    |
| `CIRCULAR`      | Import direction violates tier DAG                                                            |

---

## Audit Execution: 10 Parallel Agents

Each agent produces a structured table per repo: `Class name | File path | Classification | Recommended action | Notes`

### Agent Group Assignment

| Agent  | Repos                                                                                                                                                                                                 | Focus                                                                                                                              |
| ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| **1**  | `unified-api-contracts`, `unified-internal-contracts`                                                                                                                                                 | Full schema inventory; UAC/UIC duplicates; orphaned schemas in both; UIC→UAC import boundary; check for `domain/<service>/` in UIC |
| **2**  | `unified-events-interface`, `unified-cloud-interface`, `execution-algo-library`, `matching-engine-library`                                                                                            | T0 libs; schemas that should move to UIC; verify no forbidden UAC/UIC imports                                                      |
| **3**  | `unified-reference-data-interface`, `unified-config-interface`, `unified-trading-library`                                                                                                             | T1 libs; classify schemas; check cross-import graph; UTL/UDC existing schema access patterns                                       |
| **4**  | `unified-market-interface`, `unified-trade-execution-interface`                                                                                                                                       | T2 libs; `_<venue>_models.py` → MISPLACE-UAC; check duplicates with UAC                                                            |
| **5**  | `unified-ml-interface`, `unified-feature-calculator-library`, `unified-position-interface`, `unified-defi-execution-interface`, `unified-sports-execution-interface`, `unified-domain-client`         | T2/T3; same as Agent 4; `InstrumentKey` cross-import scope; UDC access patterns                                                    |
| **6**  | `execution-service`, `strategy-service`, `strategy-validation-service`, `risk-and-exposure-service`, `alerting-service`                                                                               | Services A; all local schemas = MISPLACE-UIC; document target UIC path per schema                                                  |
| **7**  | `market-data-processing-service`, `market-tick-data-service`, `market-data-api`, `instruments-service`, `features-calendar-service`                                                                   | Services B                                                                                                                         |
| **8**  | `features-delta-one-service`, `features-volatility-service`, `features-cross-instrument-service`, `features-multi-timeframe-service`, `features-onchain-service`, `features-sports-service`           | Services C                                                                                                                         |
| **9**  | `ml-inference-service`, `ml-training-service`, `pnl-attribution-service`, `position-balance-monitor-service`, `execution-results-api`, `client-reporting-api`, `deployment-api`, `deployment-service` | Services D + APIs                                                                                                                  |
| **10** | `unified-trading-pm/cursor-rules/`, `unified-trading-codex/`                                                                                                                                          | Rules & docs; gaps vs master rules; `schema-governance.md` service-owned pattern to retire; diff of needed changes                 |

### Search Patterns (per agent, exclude .venv\*/tests)

```bash
rg "class \w+\(.*BaseModel" --type py --glob '!.venv*' --glob '!**/tests/**'
rg "@dataclass" --type py --glob '!.venv*' --glob '!**/tests/**'
rg "class \w+\(TypedDict\)" --type py --glob '!.venv*' --glob '!**/tests/**'
rg "from unified_api_contracts|from unified_internal_contracts" --type py --glob '!.venv*'
```

---

## Audit Output Document

Path: `unified-trading-pm/plans/archive/SCHEMA_CONTRACTS_AUDIT.md`

Sections:

1. **Executive Summary** — violation counts by category, repos clean vs violated
2. **Master Schema Placement Rules** — embed finalized table
3. **Section 1: UAC/UIC Internal Audit** — inventory, duplicates, orphans, tier boundary
4. **Section 2: Violations by Repo** — per-repo tables
5. **Section 3: Aggregate Violation Catalogue** — MISPLACE-UAC | MISPLACE-UIC | DUPLICATE | CONFLICT | ORPHAN
6. **Section 4: Codex & Cursor Rules Gaps** — topic | exists-in-codex | exists-in-mdc | gap | priority | file to
   create/update
7. **Section 5: Tier Structure Assessment** — UAC/UIC dependency formalization, manifest diff
8. **Section 6: Remediation Priority Order**

---

## Codex & Cursor Rules Changes Required

### New `.mdc` rules to create:

- `imports/adapter-models-belong-in-uac.mdc` — adapter Pydantic parsers must be in UAC
- `imports/no-schema-outside-contracts.mdc` — no schema outside UAC or UIC (except CORRECT-LOCAL)
- `imports/uic-may-import-uac.mdc` — permitted UIC→UAC direction; UAC must not import UIC
- `imports/service-domain-schema-in-uic.mdc` — service domain schemas belong in UIC `domain/<service>/`; access via
  UTL/UDC

### Existing rules to update:

- `imports/contracts-integration.mdc` — add: adapter-private models are not exempt, must go to UAC
- `core/schema-service-owned.mdc` — RETIRE; replace with pointer to `service-domain-schema-in-uic.mdc`
- Codex `02-data/contracts-scope-and-layout.md` — add UIC→UAC as PERMITTED; UAC→UIC as BLOCKED even in tests;
  normalization vs messaging canonical split
- Codex `02-data/schema-governance.md` — retire service-owned `output_schemas.py` pattern; update to UIC domain schema
  pattern
- Codex `04-architecture/TIER-ARCHITECTURE.md` + `workspace-manifest.json` — formalize UAC as T0 leaf, UIC as T0b
  (UAC-dependent); split L2 into L2a (UAC) and L2b (UIC)

---

## Verification

1. Violation counts spot-checked against 3 manually reviewed repos
2. All duplicate types have both locations documented with field-level diff
3. All orphaned schemas in UAC/UIC listed in Section 3e with `[ORPHAN]` marker
4. Codex gap table maps each gap to a specific file to create/update
5. Tier assessment includes concrete `workspace-manifest.json` L2 split diff

---

## Reference

- `unified-api-contracts/unified_api_contracts/unified_normalised_contracts/domain.py` — UAC canonicals
- `unified-internal-contracts/unified_internal_contracts/market_data/__init__.py` — existing UIC→UAC imports
- `unified-internal-contracts/unified_internal_contracts/reference/instrument.py` — duplicate InstrumentRecord
- `unified-trading-pm/workspace-manifest.json` — tier structure for formalization
- `unified-trading-pm/cursor-rules/imports/contracts-integration.mdc` — existing rule to update
- `unified-trading-pm/cursor-rules/core/schema-service-owned.mdc` — rule to retire
- `unified-trading-/codex/02-data/contracts-scope-and-layout.md` — codex to update
- `unified-trading-/codex/04-architecture/TIER-ARCHITECTURE.md` — tier docs to update
