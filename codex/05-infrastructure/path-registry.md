---
doc_type: codex-ssot
title: Path Registry
summary:
  "STUB — central registry of GCS paths, service endpoints, and deployment URLs per environment. Canonical source is
  deployment-service/configs/cloud-providers.yaml, accessed via
  unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name()."
status: draft
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [infrastructure, gcs, registry, canonicalisation]
related:
  [/codex/15-runbooks/phase-2-6-bucket-name-cutover-runbook.md, /codex/05-infrastructure/gcs-object-operations.md]
created: 2026-05-21
authoritative_for: [per-environment gcs path and deployment-url registry]
referenced_by: [/codex/15-runbooks/phase-2-6-bucket-name-cutover-runbook.md]
owner:
last_reviewed: 2026-10-26
code_refs:
type: infrastructure
---

# Path Registry

> **STUB** — Reference: `plans/active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`.

Central registry of GCS paths, service endpoints, and deployment URLs per environment. Canonical source:
`deployment-service/configs/cloud-providers.yaml`. Accessed via
`unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name()`.
