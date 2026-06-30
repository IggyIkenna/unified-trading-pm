---
doc_type: codex-ssot
title: Manifest Skip Semantics
summary:
status: stub
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-21
authoritative_for:
referenced_by:
owner:
last_reviewed:
code_refs:
type: coding-standards
---

# Manifest Skip Semantics

> **STUB** — Reference: `plans/active/honest_coverage_formula_consolidation_2026_05_19.md`.

Documents when a service is permitted to skip a shard in the manifest vs when it must emit `empty_confirmed` with a
typed reason. Skip = never emit; empty_confirmed = explicit honest absence.

Key rule: no silent skips. Every expected shard either has a manifest row or a typed reason. SSOT:
`codex/02-data/availability-manifest-and-data-status.md`.
