---
doc_type: issue
title: "plan_reconciler findings — 2026-08-06 (cross-cutting tranche, dispatch agt-6c6359)"
summary: >-
  Sharded plan_reconciler run for the cross-cutting tranche only. Heavy grace coverage (~85%+ of tranche docs modified
  within 12h) meant this run was primarily DETECT+FILE, with 2 mechanical todo-format fixes applied to writable docs.
  Zero archive candidates, zero confirmed contradictions, zero done-but-unchecked flips with hard evidence. The 4 hard
  sweep failures (reference-path ratchet, AG-closeout linkage, terminal-status-archived, archive candidates) are
  corpus-wide pre-existing conditions already tracked by existing processes — not new cross-cutting-specific findings.
status: open
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-reconciler, reconciliation, findings, cross-cutting]
created: 2026-08-06
last_updated: 2026-08-06
author: plan_reconciler
source: agt-6c6359
locked_by: plan_reconciler — run complete, awaiting operator review
nature: process
related: []
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
resolved_by:
last_updated: 2026-06-27
---

## Flips verified

(None — no open todos with HARD evidence found in writable cross-cutting docs)

## Contradictions

(None confirmed — the 4 hard sweep failures are corpus-wide ratchet conditions, not cross-cutting-specific
contradictions)

## Doc-drift

(None confirmed)

## Hygiene fixes

1. **`bucket_fold_ml_2026_07_17.md:158`** — `- [~]` → `- [x]` (non-standard marker; task text says "DONE 2026-07-18"
   with completed work described)
2. **`bucket_fold_features_2026_07_17.md:95`** — `- [~]` → `- [ ]` (non-standard marker; provisioning done but scaffold
   deferred — standardised to open checkbox reflecting partial completion)

Both verified at HEAD via `grep`.

## Filed

(None — no new operator-gated findings beyond the pre-existing sweep failures)

## Archive candidates (operator review)

(None — 0 cross-cutting docs with all todos `[x]` AND unlocked AND out of grace window)

## Refuted (dropped by verify)

(None — 0 candidates reached the verify stage)

## Coverage

- **Tranche**: cross-cutting only (`asset_group: cross-cutting` + normative refs + codex in scope per shard policy)
- **Docs in tranche**: 208 total (123 plans/active/ + 65 issues/ + 20 epics/)
- **Grace (read-only)**: ~85%+ of docs modified within 12h
- **Writable (non-grace)**: ~30 docs
- **Hunters run**: inline (no sub-agent fan-out — thin-scope run; all searches direct)
- **Normative refs checked**: PLAN_FORMAT.md (not in grace), task_template.md (grace), INDEX.md (grace)
- **Sweep**: `run_hygiene_sweep.sh --ci` Phase 0 input gathered; 4 hard failures (corpus-wide ratchets)

## Plans not reached

(None — all writable cross-cutting docs checked; grace docs read-only per policy)

## Run metadata

- **Dispatch ID**: agt-6c6359
- **Review branch**: plan_reconciler/agt-6c6359
- **Model**: sonnet, effort: max
- **Fixes applied**: 2 (todo-format)
- **Findings filed**: 0
- **Verdict**: THIN run — heavy grace coverage left very little writable surface
