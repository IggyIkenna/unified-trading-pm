---
doc_type: issue
title: execution-service quality gate blocked by external instruction API size cap
summary: >-
  execution_service/api/external_instruction_api.py is 903 lines, exceeding
  the enforced 900-line file cap on the clean LDR base; this is unrelated to
  the OMS cancellation wiring.
status: resolved
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
resolved_by: verified 2026-08-21 (archival chunk-3 re-verification, this session) -- re-measured
  execution-service/execution_service/api/external_instruction_api.py at 896 lines (< 900-line cap), superseding this
  doc's own 903-line reading; the reduction landed via unrelated in-flight execution-service feature commits
  (b49a3f1a9, 0aa709f07, 4e35a09b2) after this doc was filed, not a dedicated fix
locked_by:
context_scope: [execution-service/execution_service/api/external_instruction_api.py]
---

> **🟢 ARCHIVED 2026-08-21** — `status: resolved`, zero open todos (this doc never had a Todos section — a prose-only
> QG-red stub); archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Resolution evidence carried in `resolved_by:` above. Moved during an ARCHIVE_RESOLVED
> archival-chunk pass (chunk 3, 2026-08-21).

## What I found

The execution-service quality gate and Quickmerge re-gate fail:

```text
❌ Files exceed 900 lines:
  ./execution_service/api/external_instruction_api.py: 903 L
```

The clean LDR base is also 903 lines, and the OMS change touches only `execution_service/adapters/order_adapter.py`.

## Why it matters

## Progress Log

- **2026-08-21 (archival chunk-3 re-verification)**: `wc -l` on the sibling `execution-service` checkout shows
  `execution_service/api/external_instruction_api.py` at 896 lines, under the 900-line QG cap this doc reports
  breaching at 903. No dedicated fix commit targets this file for a line-count reduction; the file's own recent commit
  history (`b49a3f1a9`, `0aa709f07`, `4e35a09b2`) shows normal feature work landing in the interim that evidently
  brought it back under the threshold. No further action needed. Archived.
