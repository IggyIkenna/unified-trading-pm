---
doc_type: plan
title: "CI/CD deployment-ui follow-ups — Repos-CI working/pending render + unit-test flake"
summary: >-
  The two deployment-ui (TS UI) items from the cicd tracker, split out because plans are role-homogeneous and these need
  the ui-developer role: render the Repos-CI working/pending state per repo (orchestrator half already shipped — UI
  render remaining), and investigate the unstable unit test flake discovered 2026-06-27 (slot-1). UI repo —
  TS/Playwright only, no Python tools; every tick needs [UI] + pw:L2 ✓ + a cited regression spec.
status: draft
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
assigned_vm: harsh_pc
assigned_role: ui-developer
drift_direction: advance-code
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
---

# CI/CD deployment-ui follow-ups

> **Independent track — no upstream dep, parallel-startable.** **Model tier: Sonnet/ui-developer.** UI repo —
> **TS/ESLint/Vitest/Playwright only, NO Python tools.** Every tick MUST carry `[UI]` + `pw:L2 ✓` + a cited regression
> spec (`codex/06-coding-standards/ui-testing-layers.md`) or the reviewer rejects the ✅.

## Tasks

- [ ] [CODE][UI] P2. deployment-ui Repos-CI `working`/`pending` state per repo — the orchestrator half is shipped; the
      UI render is remaining. Show a per-repo working/pending indicator on the Repos-CI view fed from the backend field.
      **Gate:** `pw:L2 ✓` — a repo in `working` and one in `pending` both render the correct state; cited regression
      spec.
- [ ] [TEST][UI] P3. Investigate the unstable deployment-ui unit test (flake discovered 2026-06-27 by slot-1: first
      local QG run flaked). Find the nondeterminism (unstubbed fetch/timer/order) and stabilize it. **Gate:** the test
      passes deterministically across 10 consecutive runs; `pw:L2`/vitest green; root-cause noted.

## Success criteria

- The Repos-CI working/pending state renders correctly with Playwright coverage; the flaky unit test is stabilized with
  a root-cause note.

## Codex SSOT updates

- None (UI render of an existing backend field).

## Progress Log

- 2026-06-27: Split from the cicd consolidated tracker (deployment-ui lane; ui-developer role per role-homogeneity).
  Note: the 3 pre-existing e2e reds were already fixed (deployment-ui@0f9acfc) — these are the remaining 2 UI items.
