---
doc_type: codex-ssot
title: Service Pair Flows
summary: >-
  Canonical service-to-service interaction flows (data pipeline / execution / results / deployment), the three transport
  modes (batch-GCS / live-PubSub / co-located-in-memory), and the no-Python-imports + persist-to-GCS rules.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    execution-service,
    instruments-service,
    market-data-processing-service,
    strategy-service,
  ]
scope: [engineer, admin]
tags: [pipeline, mdps, execution, mtds, instruments]
related: [/codex/04-architecture/runtime-deployment-topology.md, /codex/04-architecture/tier-and-import-architecture.md]
created: 2026-03-27
authoritative_for: [canonical service-pair interaction flows + transport-mode/persistence rules]
referenced_by: [/codex/08-workflows/config-injection.md]
owner:
last_reviewed:
code_refs:
---

# Service Pair Flows

**SSOT:** This document describes canonical service-to-service interaction flows. Runtime behavior is defined in
`deployment-service/configs/runtime-topology.yaml`. Code dependencies (imports) are validated by
`workspace-manifest.json` arch_tier.

## Transport Modes

| Mode            | Transport           | Persistence         |
| --------------- | ------------------- | ------------------- |
| Batch           | GCS (parquet)       | GCS (same write)    |
| Live            | PubSub              | GCS (separate sink) |
| Live co-located | in_memory (same VM) | GCS                 |

## Key Flows

- **Data pipeline:** instruments-service → market-data-processing-service → features-_ → ml-_ → strategy-service →
  execution-service
- **Execution:** strategy-service publishes instructions → execution-service consumes; execution-service writes results
  to GCS
- **Results:** execution-results-api reads from GCS (produced by execution-service)
- **Deployment:** deployment-api orchestrates; deployment-service holds configs and catalog

## Rules

1. **No Python imports** between services — interaction via HTTP, PubSub, GCS only
2. **Persistence:** All services persist output to GCS regardless of transport
3. **Co-located:** in_memory allowed ONLY under `co_located_vm` deployment profile

## References

- `deployment-service/configs/runtime-topology.yaml` — runtime SSOT
- `04-architecture/runtime-deployment-topology.md` — design decisions
- `04-architecture/tier-and-import-architecture.md` — tier boundaries
