---
doc_type: codex-ssot
title: Validator Coverage Matrix - 2026-02-21
summary:
  2026-02-21 matrix mapping 114 baseline validators (BASE / COD / DAT / OBS / INF / SEC / HARDENING / ARC) to service
  types (pipeline / platform / UI) with priority and applicability, plus per-type validator counts (52 pipeline, 34
  universal). Service/UI lists use retired repo names and are stale.
status: stale
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    alerting-service,
    deployment-service,
    execution-service,
    features-service,
    instruments-service,
    market-data-processing-service,
  ]
scope: [engineer, admin]
tags: [audit, validation, quality-gates, data-quality, ssot-audit]
related: [/codex/10-audit/FOUNDATIONAL-REPOS-AUDIT-2026-03-07.md, /codex/10-audit/ssot-reference-mapping.md]
created: 2026-03-27
authoritative_for: [baseline validator-to-service-type applicability matrix (2026-02-21 snapshot)]
referenced_by: [/codex/10-audit/PARSER_FIXES_AND_BOOK_SNAPSHOT_CLARIFICATION.md, codex/validators/QUICK_REFERENCE.md]
owner:
last_reviewed:
code_refs:
---

# Validator Coverage Matrix - 2026-02-21

## Overview

This document maps which baseline validators apply to which service types, showing the validation requirements for each
category of service.

## Validator Applicability Matrix

| Validator ID                     | Area           | Priority    | Pipeline | Platform | UI-Obs | UI-Control | UI-Analysis |
| -------------------------------- | -------------- | ----------- | -------- | -------- | ------ | ---------- | ----------- |
| **Configuration**                |
| BASE-01                          | config         | P1-high     | ✅       | ✅       | ✅     | ✅         | ✅          |
| COD-01                           | config         | P0-critical | ✅       | ✅       | ✅     | ✅         | ✅          |
| COD-02                           | config         | P1-high     | ✅       | ✅       | ✅     | ✅         | ✅          |
| **Observability**                |
| BASE-02                          | observability  | P0-critical | ✅       | ✅       | ✅     | ✅         | ✅          |
| BASE-03                          | observability  | P1-high     | ✅       | ✅       | ✅     | ✅         | ✅          |
| OBS-01                           | observability  | P1-high     | ✅       | ✅       | ✅     | ✅         | ✅          |
| OBS-02                           | observability  | P2-medium   | ✅       | ✅       | ✅     | ✅         | ✅          |
| OBS-03                           | observability  | P1-high     | ✅       | ✅       | ✅     | ✅         | ✅          |
| OBS-04                           | observability  | P1-high     | ✅       | ✅       | ✅     | ✅         | ✅          |
| OBS-05                           | observability  | P1-high     | ✅       | ✅       | ✅     | ✅         | ✅          |
| OBS-06                           | observability  | P1-high     | ✅       | ✅       | ✅     | ✅         | ✅          |
| **Data (Pipeline Only)**         |
| DAT-01                           | data           | P1-high     | ✅       | ❌       | ❌     | ❌         | ❌          |
| DAT-02                           | data           | P0-critical | ✅       | ❌       | ❌     | ❌         | ❌          |
| DAT-03                           | data           | P0-critical | ✅       | ❌       | ❌     | ❌         | ❌          |
| DAT-06                           | data           | P1-high     | ✅       | ❌       | ❌     | ❌         | ❌          |
| DAT-07                           | data           | P1-high     | ✅       | ✅       | ✅     | ✅         | ✅          |
| DAT-08                           | data           | P2-medium   | ✅       | ❌       | ❌     | ❌         | ❌          |
| DAT-13                           | data           | P2-medium   | ✅       | ❌       | ❌     | ❌         | ❌          |
| DAT-16                           | data           | P1-high     | ✅       | ❌       | ❌     | ❌         | ❌          |
| DAT-18                           | data           | P1-high     | ✅       | ❌       | ❌     | ❌         | ❌          |
| DAT-19                           | data           | P1-high     | ✅       | ❌       | ❌     | ❌         | ❌          |
| DAT-20                           | data           | P1-high     | ✅       | ❌       | ❌     | ❌         | ❌          |
| BASE-20                          | data           | P1-high     | ✅       | ❌       | ❌     | ❌         | ❌          |
| BASE-21                          | data           | P1-high     | ✅       | ❌       | ❌     | ❌         | ❌          |
| BASE-22                          | data           | P1-high     | ✅       | ❌       | ❌     | ❌         | ❌          |
| DAT-21                           | data           | P1-high     | ✅       | ❌       | ❌     | ❌         | ❌          |
| DAT-23                           | data           | P2-medium   | ✅       | ❌       | ❌     | ❌         | ❌          |
| **Architecture (Pipeline Only)** |
| ARC-01                           | architecture   | P1-high     | ✅       | ❌       | ❌     | ❌         | ❌          |
| ARC-02                           | architecture   | P1-high     | ✅       | ❌       | ❌     | ❌         | ❌          |
| ARC-03                           | architecture   | P1-high     | ✅       | ❌       | ❌     | ❌         | ❌          |
| ARC-08                           | architecture   | P1-high     | ✅       | ✅       | ✅     | ✅         | ✅          |
| ARC-11                           | architecture   | P2-medium   | ✅\*     | ❌       | ❌     | ❌         | ❌          |
| BASE-28                          | architecture   | P1-high     | ✅\*\*   | ❌       | ❌     | ❌         | ❌          |
| BASE-29                          | architecture   | P1-high     | ✅\*\*\* | ❌       | ❌     | ❌         | ❌          |
| **Infrastructure**               |
| INF-01                           | infrastructure | P0-critical | ✅       | ✅       | ✅     | ✅         | ✅          |
| INF-02                           | infrastructure | P0-critical | ✅       | ✅       | ✅     | ✅         | ✅          |
| INF-03                           | infrastructure | P1-high     | ✅       | ✅       | ✅     | ✅         | ✅          |
| INF-04                           | infrastructure | P1-high     | ✅       | ✅       | ✅     | ✅         | ✅          |
| INF-05                           | infrastructure | P1-high     | ✅       | ✅       | ✅     | ✅         | ✅          |
| INF-07                           | infrastructure | P1-high     | ✅       | ✅       | ✅     | ✅         | ✅          |
| INF-08                           | infrastructure | P1-high     | ✅       | ✅       | ✅     | ✅         | ✅          |
| INF-14                           | infrastructure | P3-low      | ✅       | ✅       | ✅     | ✅         | ✅          |
| INF-15                           | infrastructure | P2-medium   | ✅       | ✅       | ✅     | ✅         | ✅          |
| **Coding Standards**             |
| COD-04                           | coding         | P0-critical | ✅       | ✅       | ✅     | ✅         | ✅          |
| COD-05                           | coding         | P0-critical | ✅       | ✅       | ✅     | ✅         | ✅          |
| COD-07                           | coding         | P1-high     | ✅       | ✅       | ✅     | ✅         | ✅          |
| COD-08                           | coding         | P2-medium   | ✅       | ✅       | ✅     | ✅         | ✅          |
| COD-09                           | coding         | P2-medium   | ✅       | ✅       | ✅     | ✅         | ✅          |
| COD-10                           | coding         | P1-high     | ✅       | ✅       | ✅     | ✅         | ✅          |
| COD-14                           | coding         | P0-critical | ✅       | ✅       | ✅     | ✅         | ✅          |
| COD-16                           | coding         | P0-critical | ✅       | ✅       | ✅     | ✅         | ✅          |
| COD-17                           | coding         | P0-critical | ✅       | ✅       | ✅     | ✅         | ✅          |
| BASE-24                          | coding         | P0-critical | ✅       | ✅       | ✅     | ✅         | ✅          |
| BASE-25                          | coding         | P0-critical | ✅       | ✅       | ✅     | ✅         | ✅          |
| BASE-26                          | coding         | P0-critical | ✅       | ✅       | ✅     | ✅         | ✅          |
| **Hardening**                    |
| HARDENING-01                     | coding         | P0-critical | ✅       | ✅       | ✅     | ✅         | ✅          |
| HARDENING-02                     | coding         | P1-high     | ✅       | ✅       | ✅     | ✅         | ✅          |
| HARDENING-03                     | coding         | P1-high     | ✅       | ❌       | ❌     | ❌         | ❌          |
| HARDENING-04                     | coding         | P1-high     | ✅       | ✅       | ✅     | ✅         | ✅          |
| HARDENING-05                     | coding         | P1-high     | ✅       | ❌       | ❌     | ❌         | ❌          |
| HARDENING-06                     | coding         | P1-high     | ✅       | ❌       | ❌     | ❌         | ❌          |
| **Security**                     |
| SEC-01                           | security       | P0-critical | ✅       | ✅       | ✅     | ✅         | ✅          |
| SEC-02                           | security       | P0-critical | ✅       | ✅       | ✅     | ✅         | ✅          |
| SEC-04                           | security       | P1-high     | ✅       | ✅       | ✅     | ✅         | ✅          |
| SECURITY-03                      | security       | P0-critical | ✅       | ✅       | ✅     | ✅         | ✅          |
| SECURITY-05                      | security       | P0-critical | ✅       | ✅       | ✅     | ✅         | ✅          |
| BASE-13                          | security       | P1-high     | ✅       | ✅       | ✅     | ✅         | ✅          |
| BASE-14                          | security       | P1-high     | ✅       | ✅       | ✅     | ✅         | ✅          |
| BASE-15                          | security       | P0-critical | ✅       | ✅       | ✅     | ✅         | ✅          |
| BASE-32                          | security       | P0-critical | ✅       | ✅       | ✅     | ✅         | ✅          |
| **Libraries**                    |
| BASE-30                          | infrastructure | P1-high     | ✅       | ✅       | ✅     | ✅         | ✅          |
| BASE-31                          | infrastructure | P1-high     | ✅       | ❌       | ❌     | ❌         | ❌          |

**Footnotes:**

- \*ARC-11: Applies only to batch_and_live services
- \*\*BASE-28: Applies only to batch-mode pipeline services
- \*\*\*BASE-29: Applies only to live-mode pipeline services

## Coverage Summary by Service Type

| Service Type              | Total Validators | P0-Critical | P1-High | P2-Medium | P3-Low |
| ------------------------- | ---------------- | ----------- | ------- | --------- | ------ |
| Pipeline (batch_and_live) | 52               | 13          | 28      | 9         | 2      |
| Pipeline (batch_only)     | 50               | 13          | 27      | 8         | 2      |
| Platform                  | 34               | 13          | 15      | 5         | 1      |
| UI-Observability          | 34               | 13          | 15      | 5         | 1      |
| UI-Control                | 34               | 13          | 15      | 5         | 1      |
| UI-Analysis               | 34               | 13          | 15      | 5         | 1      |

## Pipeline Services (16 services)

**Unique validators**: 52 (34 universal + 18 pipeline-specific)

### Pipeline-Specific Validators

**Data Governance (17 validators)**:

- DAT-01 through DAT-03: Schema validation, timestamp alignment
- DAT-06, DAT-08: Output correctness, partitioning
- DAT-13, DAT-16, DAT-18: Data catalogue, completeness, dependency chain
- DAT-19, DAT-20: Normalized publish/subscribe interfaces
- BASE-20, BASE-21, BASE-22: Sharding, start dates, MVP alignment
- DAT-21, DAT-23: Expected dates, catalogue sync

**Architecture (8 validators)**:

- ARC-01 through ARC-03: Pipeline DAG, sharding config, CLI-GCS alignment
- ARC-11: Batch-live symmetry (batch_and_live services only)
- BASE-28: Batch deployment topology (batch services)
- BASE-29: Live deployment topology (live services)

**Hardening (3 validators)**:

- HARDENING-03: Known-missing vs unexpected-missing data handling
- HARDENING-05: No defensive empty-data fallbacks
- HARDENING-06: Shard-level failure isolation

### Pipeline Services List

**Batch & Live (14 services)**:

- instruments-service
- features-service (calendar family) (includes `corporate_actions` data path)
- market-tick-data-service
- market-data-processing-service
- features-service (delta-one family)
- features-service (volatility family)
- features-service (onchain family)
- features-service (sports family)
- ml-inference-service
- strategy-service
- execution-service
- position-balance-monitor-service
- risk-and-exposure-service
- pnl-attribution-service

**Batch Only (1 service)**:

- ml-training-service

## Platform Services (5 services)

**Unique validators**: 34 (34 universal, 0 platform-specific)

Platform services share the same universal validators as UI services but do not have pipeline-specific data/architecture
validators.

### Platform Services List

- unified-trading-services
- deployment-service
- unified-trading-codex
- exchange-interface-library
- alerting-service

## UI Services (9 services)

**Unique validators**: 34 (34 universal, 0 UI-specific)

UI services (observability, control, analysis) all share the same validator set.

### UI-Observability (3 services)

- live-health-monitor-ui
- batch-audit-ui
- logs-dashboard-ui

### UI-Control (1 service)

- ml-training-ui

### UI-Analysis (5 services)

- execution-analytics-ui
- trading-analytics-ui
- settlement-ui
- client-reporting-ui
- strategy-onboarding-ui

## Universal Validators (All 30 Services)

These 34 validators apply to **every service** regardless of type:

### Configuration (3)

- BASE-01, COD-01, COD-02

### Observability (7)

- BASE-02, BASE-03, OBS-01 through OBS-06

### Data (Storage) (1)

- DAT-07 (cloud-agnostic storage client usage)

### Architecture (Communication) (1)

- ARC-08 (correct communication pattern)

### Infrastructure (9)

- INF-01 through INF-05, INF-07, INF-08, INF-14, INF-15

### Coding Standards (12)

- COD-04, COD-05, COD-07 through COD-10
- COD-14, COD-16, COD-17
- BASE-24, BASE-25, BASE-26

### Hardening (2)

- HARDENING-01, HARDENING-02, HARDENING-04

### Security (9)

- SEC-01, SEC-02, SEC-04
- SECURITY-03, SECURITY-05
- BASE-13, BASE-14, BASE-15, BASE-32

### Libraries (1)

- BASE-30 (correct UCI/UCS/UEI usage)

## Priority Distribution

| Priority    | Pipeline | Platform | UI Services | Total Across All          |
| ----------- | -------- | -------- | ----------- | ------------------------- |
| P0-critical | 13       | 13       | 13          | 13 (same validators)      |
| P1-high     | 28       | 15       | 15          | 41 (13 pipeline-specific) |
| P2-medium   | 9        | 5        | 5           | 18 (4 pipeline-specific)  |
| P3-low      | 2        | 1        | 1           | 2 (1 pipeline-specific)   |

## Validation Execution Order

### Phase 1: Universal P0-Critical (All 30 Services)

1. BASE-01, COD-01: Config management
2. BASE-02, OBS-05, OBS-06: Event logging
3. COD-04, COD-05: Error handling
4. BASE-24, BASE-25, BASE-26: Quality gates
5. SEC-01, SECURITY-03, BASE-15, BASE-32: Security basics

### Phase 2: Pipeline P0-Critical (16 Services)

1. DAT-02, DAT-03: Schema validation, timestamp alignment

### Phase 3: Universal P1-High (All 30 Services)

1. BASE-03, OBS-01, OBS-03, OBS-04: Observability
2. INF-02 through INF-05, INF-07, INF-08: Infrastructure
3. COD-16, COD-17: Quality gates
4. BASE-30, HARDENING-01, HARDENING-02: Libraries and hardening

### Phase 4: Pipeline P1-High (16 Services)

1. BASE-20, BASE-21, BASE-22: Sharding, start dates, MVP
2. DAT-01, DAT-06, DAT-07, DAT-16, DAT-18, DAT-19, DAT-20, DAT-21: Data governance
3. ARC-01, ARC-02, ARC-03: Architecture
4. HARDENING-03, HARDENING-04, HARDENING-05, HARDENING-06: Hardening

### Phase 5: P2-Medium & P3-Low (All Services)

1. Remaining validators by priority

---

**Generated**: 2026-02-21 **Total Validators**: 114 unique **Total Baseline Items**: 5,016 (across 44 audit files)
