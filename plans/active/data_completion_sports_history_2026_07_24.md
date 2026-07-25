---
doc_type: plan
title: Data completion to 100% — Sports — Shipped History (forked from the sports data-completion plan)
summary: >-
  MOVED. This doc is now archived at plans/archive/2026_07/data_completion_sports_history_2026_07_24.md — confirmed zero
  open todos by the 2026-07-25 orphan-audit workflow, archived via the standard 6-step ritual. This stub exists only
  because a concurrent commit (`9aed72662`) landed the archive-path copy but silently dropped the `git rm` half of the
  move, and `git rm` is blocked for autonomous workers by agent-orchestrator's `block_destructive_commands.py` guardrail
  (correctly — the operator should confirm a delete). Queued for the operator in
  plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md — this file should simply be `git rm`'d once
  confirmed.
status: complete
nature: record
asset_group: [sports]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-api-contracts, deployment-service]
scope: [engineer, admin]
tags: [sports, history, archive-bound, stale-duplicate-stub]
related:
  [
    /plans/archive/2026_07/data_completion_sports_history_2026_07_24.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-25"
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: docs_reconciler
drift_direction: advance-code
supersedes:
superseded_by: data_completion_sports_history_2026_07_24
depends_on:
source: >-
  Stale-duplicate stub created 2026-07-25 after a concurrent commit half-landed this doc's archival move — see summary.
locked_by:
locked_since:
---

# Data completion to 100% — Sports — Shipped History (STALE DUPLICATE — see plans/archive/2026_07/data_completion_sports_history_2026_07_24.md)

> **⚠️ STALE DUPLICATE.** The real, current version of this doc lives at
> `plans/archive/2026_07/data_completion_sports_history_2026_07_24.md` (archived 2026-07-25, zero open todos). This file
> is a leftover from a half-landed `git mv` (a concurrent commit picked up the archive-path ADD but not this file's
> DELETE). Safe to `git rm` — queued for the operator since `git rm` is guardrail-blocked for autonomous workers.

## Todos

- [ ] [OPERATOR] P3. `git rm plans/active/data_completion_sports_history_2026_07_24.md` (this file) — the real content
      is at `plans/archive/2026_07/data_completion_sports_history_2026_07_24.md`. **Done when**: this file no longer
      exists.
