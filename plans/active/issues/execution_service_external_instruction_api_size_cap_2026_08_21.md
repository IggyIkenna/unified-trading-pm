---
doc_type: issue
title: execution-service quality gate blocked by external instruction API size cap
summary: >-
  execution_service/api/external_instruction_api.py is 903 lines, exceeding
  the enforced 900-line file cap on the clean LDR base; this is unrelated to
  the OMS cancellation wiring.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service]
scope: [engineer]
tags: [execution-service, quality-gates, file-size, repo-blocker]
related: [/plans/active/cross_cutting_consolidated_closeout_2026_07_25.md, /plans/epics/system_readiness_master.md]
created: 2026-08-21
author: agent
parent_epic: system_readiness_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
source: [execution-service quality-gates.sh, worker task w_execution_orchestrator_oms_persistence_impl-3a3497b9442d]
resolved_by:
locked_by:
context_scope: [execution-service/execution_service/api/external_instruction_api.py]
---

## What I found

The execution-service quality gate and Quickmerge re-gate fail:

```text
❌ Files exceed 900 lines:
  ./execution_service/api/external_instruction_api.py: 903 L
```

The clean LDR base is also 903 lines, and the OMS change touches only `execution_service/adapters/order_adapter.py`.

## Why it matters
