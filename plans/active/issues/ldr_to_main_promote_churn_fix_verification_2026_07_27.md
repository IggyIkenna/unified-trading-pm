---
doc_type: issue
title: Verify the no-preempt-in-flight-validation fix actually cuts promote-PR quality-gates-v2 churn
summary: >
  Tracking note for the fix shipped this session in `ldr-to-main-promote.yml` / `ldr-to-main-promote-fleet.yml` (commit
  `48800b7ad`, merged to `main` via PR #1674): the promote bots no longer supersede an open `chore(promote)` PR the
  moment LDR's tip moves — they now wait until that PR's `quality-gates-v2` run reaches a terminal state before cutting
  a fresh snapshot. Prior behavior measured ~15-20 wasted `quality-gates-v2` runs before one attempt survived long
  enough to merge (observed on PM directly). This doc exists to record the first live before/after measurement rather
  than leave the claim theoretical.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci-cd, quality-gates-v2, promote-bot, verification]
related: [/codex/08-workflows/ci-cd-flow.md]
created: 2026-07-27
parent_epic: infrastructure_master
priority: P3
source: operator request, 2026-07-27 — "ship a small change then confirm churn has improved"
assigned_vm: NA
execution_scope: local-only
assigned_role: infra
drift_direction: advance-code
last_updated: 2026-07-27
locked_by:
resolved_by:
depends_on: []
---

# Verifying the promote-PR churn fix

## Todos

- [ ] [VERIFY] P3. This commit itself is the test case: ship via quickmerge, then count how many `quality-gates-v2` runs
      fire against the resulting `chore(promote)` PR's head SHA before it merges
      (`gh run list --repo IggyIkenna/unified-trading-pm --workflow=quality-gates-v2.yml --json headSha,createdAt`
      filtered to that PR's head). Expect ~1-2 runs (vs. the pre-fix 15-20) — record the actual count here once
      observed, then archive this doc with the result.
