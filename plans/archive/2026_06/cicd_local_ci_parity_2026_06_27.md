---
doc_type: plan
title: CI/CD local↔CI parity (WS-D) — drive the gate to byte-identical + churn-protection + e2e conflict test
summary:
  WS-D drive-to-parity. Fix any non-SIT-delta divergence in the local↔CI matrix to byte-identical so a local
  quality-gates.sh green reliably predicts a server quality-gates-v2 green. Add churn-protection
  (manifest-canonical-form so the manifest stops re-serializing differently) and an e2e merge-conflict test that forces
  a conflict PR across separate Path-B clones to exercise quickmerge STAGE 0.4 auto-reconcile. Independent of Phase-2.
status: superseded
nature: process
asset_group: cross-asset
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [cicd, WS-D, local-ci-parity, churn-protection, quickmerge, manifest-canonical-form]
related:
  [
    /plans/archive/2026_06/cicd_consolidated_remaining_2026_06_24.md,
    ../epics/infrastructure_master.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: 2026-06-27
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
last_updated: 2026-06-30
locked_by: live-defi-rollout
locked_since: 2026-06-27
supersedes:
superseded_by: cicd_mvp_ldr_to_main_pipeline_2026_06_30.md
depends_on:
source: cicd_consolidated_remaining_2026_06_24.md (WS-D lines ~1387, 1405, 1423)
assigned_role: infra
drift_direction: advance-code
---

# CI/CD local↔CI parity (WS-D)

> **Independent track — no upstream dep, parallel-startable.** **Model tier: Sonnet/infra.** Tightens
> local-green→promote-green (complements the irreducible promote-time v2; it does NOT remove it — D11: local QG runs on
> the pre-pull tree, the promote tip is a concurrent combination).

## Tasks

- [ ] [SCRIPT] P1. Fix any non-SIT-delta divergence in the local↔CI matrix to byte-identical — the drive-to-parity goal.
      Enumerate every check that differs between `quality-gates.sh` (local) and `quality-gates-v2` (server) and
      reconcile to identical behaviour (versions, flags, ordering). **Gate:** a curated diff repo passes/fails
      identically local vs v2; the parity matrix shows zero non-SIT deltas.
- [ ] [INFRA] P2. Churn-protection: manifest-canonical-form (the manifest serializes deterministically so it stops
      re-emitting cosmetically-different bytes) + a guard that rejects non-canonical manifest writes. (idempotent
      plan-inventory regen already ✅.) **Gate:** repeated manifest writes are byte-stable; a non-canonical write is
      rejected.
- [ ] [INFRA] P2. E2e smoke: force a merge-conflict PR across SEPARATE Path-B clones → quickmerge STAGE 0.4
      auto-reconcile is exercised end-to-end. **Gate:** the e2e test creates a real cross-clone conflict and asserts
      STAGE 0.4 reconciles (or exits with the structured QUICKMERGE_BLOCKED on a genuine same-file conflict).

## Success criteria

- The local↔CI matrix is byte-identical (zero non-SIT deltas); manifest writes are canonical/idempotent; the quickmerge
  conflict-reconcile path has e2e coverage.

## Codex SSOT updates

- `/codex/06-coding-standards/quality-gates.md` — note the local↔v2 parity guarantee + manifest-canonical-form.

## Progress Log

- 2026-06-27: Split from the cicd consolidated tracker (WS-D parity lane). Independent — parallel.
