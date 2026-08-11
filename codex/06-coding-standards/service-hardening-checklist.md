---
doc_type: codex-ssot
title: Service Hardening Checklist
summary: >-
  Forwarder stub — the D1→D5 service-hardening progression, per-gate checklists, QG structure verification, and
  tier-promotion criteria moved 2026-05-08 (codex_refactor Phase D.7) to README.md § Production Readiness Checklist;
  retained read-only because cursor-rules + PM plans reference it directly.
status: superseded
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [service-hardening, quality-gates, refactor]

  [
    /codex/06-coding-standards/README.md,
    /codex/06-coding-standards/integration-testing-layers.md,
    /codex/06-coding-standards/validation-and-errors.md,
  ]
created: 2026-03-27
authoritative_for: []
referenced_by:
owner:
last_reviewed:
code_refs:
---

# Service Hardening Checklist

> **Moved 2026-05-08 (codex_refactor Phase D.7).** The D1→D5 progression, per-gate checklists, QG structure
> verification, and tier promotion criteria now live in
> [`README.md` § Production Readiness Checklist § Service Hardening: D1→D5 progression](./README.md#service-hardening-d1d5-progression).
>
> This file is retained as a forwarder stub because cursor-rules + a few PM plans + the master readiness doc reference
> it directly. New writes go to README; this file is read-only.

## Cross-references

- **Canonical SSOT**: [`README.md` § Production Readiness Checklist](./README.md#production-readiness-checklist)
- **Phase 2 plan**: `unified-trading-pm/plans/archive/phase2_library_tier_hardening.plan.md`
- **Phase 3 plan**: `unified-trading-pm/plans/archive/phase3_service_hardening_integration.plan.md`
- **Quality gates template**: `unified-trading-pm/codex/06-coding-standards/quality-gates-service-template.sh`
- **Integration testing layers**: `unified-trading-pm/codex/06-coding-standards/integration-testing-layers.md`
- **Validation + errors standards**: `unified-trading-pm/codex/06-coding-standards/validation-and-errors.md`
