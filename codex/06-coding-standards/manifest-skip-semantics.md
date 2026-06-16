---
scope: [engineer, admin]
title: Manifest Skip Semantics
type: coding-standards
status: stub
created: 2026-05-21
---

# Manifest Skip Semantics

> **STUB** — Reference: `plans/active/honest_coverage_formula_consolidation_2026_05_19.md`.

Documents when a service is permitted to skip a shard in the manifest vs when it must emit `empty_confirmed` with a
typed reason. Skip = never emit; empty_confirmed = explicit honest absence.

Key rule: no silent skips. Every expected shard either has a manifest row or a typed reason. SSOT:
`codex/02-data/availability-manifest-and-data-status.md`.
