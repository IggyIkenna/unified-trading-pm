---
doc_type: issue
title: Fix stale SSOT citations in 7 remaining domain smoke_matrix.py files (e2e-testing)
summary: >-
  7 domain smoke_matrix.py files in e2e-testing/scripts/ still reference the dead launch-features-backfill-vm.sh and the
  archived institutional_smoke_matrix_2026_04_20 plan. Found while fixing the sports file
  (infra_satellite_ao_dispatch_batch2-004). Citation-only.
status: resolved
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [e2e-testing, unified-trading-pm]
scope: [engineer, admin]
tags: [doc-fix, smoke-matrix, stale-citations, e2e-testing]
related: [/plans/archive/2026_08/infra_satellite_ao_dispatch_batch2_2026_07_27.md]
created: "2026-08-04"
author: unknown
last_updated: "2026-08-04"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.08
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
resolved_by: e2e-testing@2bee452
supersedes:
superseded_by:
depends_on: []
source: >-
  Found by slot-7 infra agent while fixing infra_satellite_ao_dispatch_batch2-004 (sports smoke_matrix.py). The other 7
  domain smoke_matrix.py files in e2e-testing have the identical stale citation pattern.
---

# Fix stale SSOT citations in 7 remaining domain smoke_matrix.py files

## What I found

While fixing the sports smoke_matrix.py (task infra_satellite_ao_dispatch_batch2-004, e2e-testing@e117593), I found that
7 other smoke_matrix.py files in e2e-testing/scripts/ share the exact same stale citations:

- `launch-features-backfill-vm.sh` (dead; replaced by `launch-features-vm.sh`)
- `institutional_smoke_matrix_2026_04_20` plan (archived at plans/archive/)

Affected files:

- `e2e-testing/scripts/calendar/smoke_matrix.py` (lines 7-9, 26)
- `e2e-testing/scripts/cross_instrument/smoke_matrix.py` (lines 7-8)
- `e2e-testing/scripts/commodity/smoke_matrix.py` (lines 7-8)
- `e2e-testing/scripts/delta_one/smoke_matrix.py` (lines 7-9, 25)
- `e2e-testing/scripts/multi_timeframe/smoke_matrix.py` (lines 7-8)
- `e2e-testing/scripts/onchain/smoke_matrix.py` (lines 7-9, 25)
- `e2e-testing/scripts/volatility/smoke_matrix.py` (lines 7-8)

## Why it matters

Stale citations mislead future maintainers about where the cell matrix is defined and which plan describes the 3-step
contract.

## Recommended decision

Replace stale citations fleet-wide (same 2-citation swap that fixed the sports file):

- `launch-features-backfill-vm.sh` → `launch-features-vm.sh` (cell map)
- `plans/active/institutional_smoke_matrix_2026_04_20.plan.md` (archived) →
  `/codex/15-runbooks/smoke-testing-playbook.md`

## Todos

- [x] ✅ [DOC] P3. Fix stale SSOT citations in the 7 remaining e2e-testing smoke_matrix.py files (calendar,
      cross_instrument, commodity, delta_one, multi_timeframe, onchain, volatility) — same swap as sports:
      `launch-features-backfill-vm.sh` → `launch-features-vm.sh`,
      `plans/active/institutional_smoke_matrix_2026_04_20.plan.md` → `/codex/15-runbooks/smoke-testing-playbook.md`.
      Repo: e2e-testing. Done when: all 7 files cite only current, live docs and `quality-gates.sh` green —
      e2e-testing@2bee452
