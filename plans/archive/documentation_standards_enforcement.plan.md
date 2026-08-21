---
doc_type: plan
title: Documentation Standards Enforcement
summary: 'Enforce the service-canonical and library-canonical documentation standards (audit S5.1–S5.10)

  across all repos. Most docs are well-established (ARCHITECTURE.md 35+ repos,

  CONFIGURATION.md 22+ repos, QUALITY_GATE_BYPASS_AUDIT.md 59+ repos). Gaps are:

  DEPLOYMENT_GUIDE.md missing from core services (execution, strategy, ml-training),

  docs/SCHEMA_VALIDATION.md and docs/GCS_PATHS.md not confirmed in all services,

  and stub docs that need real content. This plan audits per-type, fills gaps, and

  verifies no docs use hardcoded project IDs or bucket names.'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-05"
todos:
  - {
      id: config-injection-codex,
      content:
        "Add /codex/08-workflows/config-injection.md with architecture ASCII diagram, domain schema reference, how to
        add a new domain, service wiring pattern, UI usage guide. (Migrated from config_dynamic_injection.md p4-codex.)
        RESOLVED 2026-03-08: File already exists at unified-trading-/codex/08-workflows/config-injection.md (358 lines),
        covers all required sections: architecture ASCII, domain schemas (Instrument/Strategy/Client/Venue), adding a
        new domain, service wiring pattern, UI usage guide, anti-patterns, quality gate.",
      status: completed,
    }
  - {
      id: docs-audit-services,
      content:
        "Audit all service repos for S5.1 required docs: README.md, docs/ARCHITECTURE.md, docs/CONFIGURATION.md,
        docs/GCS_PATHS.md, docs/DEPLOYMENT_GUIDE.md, docs/TESTING.md, docs/SCHEMA_VALIDATION.md,
        QUALITY_GATE_BYPASS_AUDIT.md. Produce a gap table (repo × doc = present/stub/missing). RESOLVED 2026-03-09:
        Audited all 26 service repos. Result: 100% compliant — zero missing files, zero stubs. All repos have all 8
        required docs. Gap report: unified-trading-pm/reports/docs_gap_report_2026_03_08.md.",
      status: completed,
    }
  - {
      id: docs-audit-libraries,
      content:
        "Audit all library repos for S5.2 required docs: README.md, docs/ARCHITECTURE.md, docs/CONFIGURATION.md,
        docs/TESTING.md, QUALITY_GATE_BYPASS_AUDIT.md. Produce a gap table (repo × doc = present/stub/missing). RESOLVED
        2026-03-09: Audited all 17 library repos. 15/17 fully compliant. 2 repos with gaps: execution-algo-library
        (missing ARCHITECTURE.md, CONFIGURATION.md, TESTING.md) and unified-sports-execution-interface (same 3 docs
        missing). Stub files created for all 6 missing docs. Gap report:
        unified-trading-pm/reports/docs_gap_report_2026_03_08.md.",
      status: completed,
    }
  - {
      id: docs-fill-service-gaps,
      content:
        "Create missing service-canonical docs identified in docs-audit-services. Priority: docs/DEPLOYMENT_GUIDE.md for
        execution-service, strategy-service, ml-training-service, risk-and-exposure-service. Then
        docs/SCHEMA_VALIDATION.md and docs/GCS_PATHS.md for services that lack them. NOTE 2026-03-09:
        docs-audit-services found zero missing docs in service repos — all 26 services are fully compliant. No service
        gap fills required. Marking in-progress as no-op; library stubs (6 files) created under docs-audit-libraries.
        Full content authoring tracked under docs-fill-library-gaps.",
      status: completed,
    }
  - {
      id: docs-fill-library-gaps,
      content:
        "RESOLVED 2026-03-09: Wrote real content (replacing TODO stubs) for 6 missing library docs:
        execution-algo-library/docs/ARCHITECTURE.md, CONFIGURATION.md, TESTING.md and
        unified-sports-execution-interface/docs/ARCHITECTURE.md, CONFIGURATION.md, TESTING.md. All now meet minimum doc
        content standards (purpose, components, data flow, config fields, test commands).",
      status: completed,
    }
  - {
      id: docs-stub-check,
      content:
        "RESOLVED 2026-03-09: All stubs were in execution-algo-library and unified-sports-execution-interface (both
        identified by docs-audit-libraries). Both repos now have full content. No other stubs found in required doc
        locations across 26 service repos (docs-audit-services confirmed 100% compliant).",
      status: completed,
    }
  - {
      id: docs-no-hardcoded-ids,
      content:
        "RESOLVED 2026-03-09: Scanned all docs/ directories for 'odum-', 'trading-prod-', 'trading-staging-',
        'central-element-323112'. Hits found only in issues/, examples/, and historical audit reports — NOT in any
        required docs/ (ARCHITECTURE.md, CONFIGURATION.md, etc.). Zero fixes required in canonical doc locations.",
      status: completed,
    }
isProject: false
---

# Documentation Standards Enforcement

**Day:** 2–3 (March 6–7) **Scope:** All service repos + library repos **Blocks:** trading_system_audit_prompt S5
**Owner:** Person A (services T0–T2) + Person B (T3 + services)

---

## Blockers

| Blocker                                         | Type          | Specific Dependency                                                                       | Resolution                                                                                                              |
| ----------------------------------------------- | ------------- | ----------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Phase 0 baseline not established                | `[PLAN_TODO]` | [phase0_standards_enforcement.md](phase0_standards_enforcement.md) § todo `p0-gate-check` | Phase 0 records pass/fail per repo; docs audit should use that baseline to know which repos are already compliant       |
| docs/GCS_PATHS.md content requires bucket names | `[INFRA]`     | GCP project confirmed and buckets defined in runtime-topology.yaml                        | GCS_PATHS.md cannot use `{project_id}` if bucket structure is not yet finalized; may document with placeholders for now |

---

## Current State

| Doc Type                     | Repos With It | Known Gaps                                                                                       |
| ---------------------------- | ------------- | ------------------------------------------------------------------------------------------------ |
| README.md                    | All (52+)     | None known                                                                                       |
| docs/ARCHITECTURE.md         | 35+ repos     | Strategy-service has it at root (not docs/) — standardize                                        |
| docs/CONFIGURATION.md        | 22+ repos     | Some services may be missing                                                                     |
| QUALITY_GATE_BYPASS_AUDIT.md | 59+ repos     | Well covered                                                                                     |
| docs/DEPLOYMENT_GUIDE.md     | 12 confirmed  | **Missing: execution-service, strategy-service, ml-training-service, risk-and-exposure-service** |
| docs/SCHEMA_VALIDATION.md    | Unknown       | Must audit                                                                                       |
| docs/GCS_PATHS.md            | Unknown       | Must audit                                                                                       |
| docs/TESTING.md              | Unknown       | Must audit                                                                                       |

---

## Required Docs Per Type (S5.1 / S5.2)

### Service repos (`service-canonical`)

1. `README.md`
2. `docs/ARCHITECTURE.md`
3. `docs/CONFIGURATION.md`
4. `docs/GCS_PATHS.md`
5. `docs/DEPLOYMENT_GUIDE.md`
6. `docs/TESTING.md`
7. `docs/SCHEMA_VALIDATION.md`
8. `QUALITY_GATE_BYPASS_AUDIT.md`

### Library repos (`library-canonical`)

1. `README.md`
2. `docs/ARCHITECTURE.md`
3. `docs/CONFIGURATION.md`
4. `docs/TESTING.md`
5. `QUALITY_GATE_BYPASS_AUDIT.md`

### UI repos (`ui-canonical`) — WARN only, not blocking

1. `README.md`
2. `docs/ARCHITECTURE.md`
3. `docs/DEPLOYMENT_GUIDE.md`
4. `docs/TESTING.md`

---

## Audit Script (Per Repo)

```bash
# Check for required service-canonical docs
REQUIRED_SERVICE_DOCS=(
  "README.md"
  "docs/ARCHITECTURE.md"
  "docs/CONFIGURATION.md"
  "docs/GCS_PATHS.md"
  "docs/DEPLOYMENT_GUIDE.md"
  "docs/TESTING.md"
  "docs/SCHEMA_VALIDATION.md"
  "QUALITY_GATE_BYPASS_AUDIT.md"
)

for doc in "${REQUIRED_SERVICE_DOCS[@]}"; do
  if [ ! -f "$doc" ]; then
    echo "MISSING: $doc"
  elif [ $(wc -l < "$doc") -le 3 ]; then
    echo "STUB: $doc"
  fi
done
```

### Hardcoded ID scan

```bash
grep -rn "odum-\|trading-prod-\|trading-staging-" docs/ README.md 2>/dev/null
```

---

## Minimum Doc Content Standards

A doc is not a stub if it contains:

- **ARCHITECTURE.md**: purpose, component diagram (text or ASCII), key classes/modules, data flows
- **CONFIGURATION.md**: config class name, all fields with types and defaults, secrets list
- **DEPLOYMENT_GUIDE.md**: prerequisites, deployment steps, rollback procedure, health check URL
- **GCS_PATHS.md**: bucket name pattern, all path templates with variable descriptions
- **SCHEMA_VALIDATION.md**: schema location, validation approach, example pass/fail
- **TESTING.md**: how to run tests, coverage target, known exclusions

---

## Execution Order

1. Run audit script on all service repos → produce gap table
2. Run audit script on all library repos → produce gap table
3. Fill service gaps (DEPLOYMENT_GUIDE first — highest priority for audit)
4. Fill library gaps
5. Expand stubs
6. Scan and fix hardcoded IDs
7. Commit per-repo via quickmerge

---

## Gate Criteria

- All service repos have all 8 required docs (no missing, no stub)
- All library repos have all 5 required docs (no missing, no stub)
- Zero docs contain hardcoded GCP project IDs or bucket names
- strategy-service ARCHITECTURE.md moved to docs/ (if at root)
- All QUALITY_GATE_BYPASS_AUDIT.md files are current (Phase 0 ensures this)
