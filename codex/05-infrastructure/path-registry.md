---
doc_type: codex-ssot
title: Path Registry
summary:
status: stub
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-21
authoritative_for:
referenced_by:
owner:
last_reviewed:
code_refs:
type: infrastructure
---

# Path Registry

> **STUB** — Reference: `plans/active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`.

Central registry of GCS paths, service endpoints, and deployment URLs per environment. Canonical source:
`deployment-service/configs/cloud-providers.yaml`. Accessed via
`unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name()`.
