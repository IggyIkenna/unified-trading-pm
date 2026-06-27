---
doc_type: plan
title: CI/CD deployment-ui follow-ups — Repos-CI working/pending render + unit-test flake
summary:
  "The two deployment-ui (TS UI) items from the cicd tracker, split out because plans are role-homogeneous and these
  need the ui-developer role: render the Repos-CI working/pending state per repo (orchestrator half already shipped — UI
  render remaining), and investigate the unstable unit test flake discovered 2026-06-27 (slot-1). UI repo —
  TS/Playwright only, no Python tools; every tick needs [UI] + pw:L2 ✓ + a cited regression spec."
status: active
nature: design
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-ui]
scope: [engineer, admin]
tags: [cicd, deployment-ui, ui, repos-ci, flaky-test, ui-developer]
related:
  [
    cicd_consolidated_remaining_2026_06_24.md,
    ../epics/infrastructure_master.md,
    ../../codex/06-coding-standards/ui-testing-layers.md,
  ]
created: 2026-06-27
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
estimate_class: design
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.2
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-06-27
supersedes:
superseded_by:
depends_on:
source: cicd_consolidated_remaining_2026_06_24.md (lines ~1583, 1658)
assigned_role: ui-developer
drift_direction: advance-code
---

# CI/CD deployment-ui follow-ups

> **Independent track — no upstream dep, parallel-startable.** **Model tier: Sonnet/ui-developer.** UI repo —
> **TS/ESLint/Vitest/Playwright only, NO Python tools.** Every tick MUST carry `[UI]` + `pw:L2 ✓` + a cited regression
> spec (`codex/06-coding-standards/ui-testing-layers.md`) or the reviewer rejects the ✅.

## Tasks

- [x] ✅ [CODE][UI] P2. deployment-ui Repos-CI `working`/`pending` state per repo — deployment-api@fc440aa (Gap-4
      escalations proxy `/api/repo-ci/escalations`) + deployment-ui@9e91fa2 (Agent column with blue "agent working" /
      yellow "agent queued" chips via `repoOrchestratorState`). **pw:L2 ✓** — 32/32 smoke tests pass incl. new
      regression spec
      `repos-tab.spec.ts "Agent column renders working (dispatched) and pending (queued) orchestrator     states"`
      verifying greeks-service=dispatched and execution-service=queued.
- [x] ✅ [TEST][UI] P3. Flaky deployment-ui unit test stabilized — deployment-ui@89fd95a. **Root-cause:** debounce
      `useEffect` in `DataStatusDrilldown.tsx:508` had early `return` without cleanup in the `s.length === 0` branch; a
      100ms timer could fire into a torn-down jsdom environment → `ReferenceError: window is not defined`. **Fix:**
      restructured to always return a cleanup function that clears `debounceRef.current`. **Gate:** 10/10 consecutive
      vitest runs clean (896 passed | 16 skipped each). Regression test added:
      `DataStatusDrilldown.test.tsx "debounce timer is cancelled on unmount — no post-unmount state update"` using fake
      timers. **pw:L2 ✓** — 32/32 repos-tab smoke tests pass.

## Success criteria

- The Repos-CI working/pending state renders correctly with Playwright coverage; the flaky unit test is stabilized with
  a root-cause note.

## Codex SSOT updates

- None (UI render of an existing backend field).

## Progress Log

- 2026-06-27: Split from the cicd consolidated tracker (deployment-ui lane; ui-developer role per role-homogeneity).
  Note: the 3 pre-existing e2e reds were already fixed (deployment-ui@0f9acfc) — these are the remaining 2 UI items.
- 2026-06-27 (slot-2): **PLAN COMPLETE.** P3 (flaky test): traced `ReferenceError: window is not defined` on run 5/10 to
  missing debounce cleanup in `DataStatusDrilldown.tsx` — always-returned cleanup fn + fake-timer regression test; 10/10
  runs clean. P2 (Gap-4): shipped deployment-api proxy (`GET /api/repo-ci/escalations`) + deployment-ui Agent column
  (blue `working` / yellow `pending` chips via `repoOrchestratorState`). Both quickmerged. All 32/32 pw:L2 smoke tests
  pass.
