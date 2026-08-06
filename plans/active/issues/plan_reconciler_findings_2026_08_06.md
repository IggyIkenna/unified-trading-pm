---
doc_type: issue
title: Daily plan-reconciler findings 2026-08-06 (dispatch agt-4fdce1)
summary:
  Run-findings + progress journal for the daily deep plan-reconciliation pass (dispatch `agt-4fdce1`, slot 2). Fan-out
  DETECT (epic-cluster / topic / codex-alignment / mechanical-adjudicator / missed-flip hunters) + adversarial VERIFY,
  then APPLY the confirmed-easy and ROUTE the hard. Appended to throughout the run — see sections below for current
  state.
status: open
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, reconciliation, plan_reconciler, boot-prompt, scheduled]
related: []
created: 2026-08-06
author: plan_reconciler
parent_epic: plan_hygiene_master
priority: P2
source: ["daily plan-reconciliation pass agt-4fdce1 2026-08-06"]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-06
---

# Daily plan-reconciler findings 2026-08-06 (agt-4fdce1)

Slot 2, branch `plan_reconciler/agt-4fdce1`. This doc is the run journal — appended to as the pass progresses.

## Run context

- Now: 2026-08-06 00:09 UTC. Grace cutoff (12h): 2026-08-05 12:09 UTC.
- Corpus: 235 `plans/active/*.md` + 468 `plans/active/issues/*.md` = 703 candidate files. **300/703 (43%) are within the
  12h grace window** — a much higher fraction than typical, meaning several large bulk commits landed in the last 12h
  touching a wide swath of the corpus. These are read-only context this run; nothing in the grace set is written.
- `run_hygiene_sweep.sh --ci`: 5 hard ratchet failures, 1 soft warning (full detail below). Inventory regenerator: 232
  active plans, 5 orphans, 0 TBD, 62% done overall, 274 cal AI-days left. INDEX.md regenerated (232 plans, 0
  uncategorized) — this + the archive inventory-dashboard regen are mechanical, kept (not the same class of side effect
  as the `master_to_live_defi` grace-plan revert, which WAS discarded per STEP 1 instructions).

## Hard ratchet failures (Phase-0 inventory from the sweep)

| Check                       |              Baseline |                  Live |                Delta | My scope this run                                                       |
| --------------------------- | --------------------: | --------------------: | -------------------: | ----------------------------------------------------------------------- |
| Terminal-status-archived    |                     1 |                    33 |                  +32 | FIX — archive ritual (STEP 5f), grace/lock permitting                   |
| Archive candidates          |                     0 |                   147 |                 +147 | FIX — archive ritual (STEP 5f), grace/lock permitting; overlaps row 1   |
| Reference paths (format)    |                    81 |                   103 |                  +22 | FIX — `fix_reference_paths.py` mechanical pass, grace-filtered          |
| Reference paths (existence) |                    86 |                   103 |                  +17 | MIXED — mechanical adjudicator per dangling ref; route what's ambiguous |
| AG-closeout linkage         |                    69 |                    87 |                  +18 | ROUTE — `/ag-closeout-audit` scope, not hand-fixed here (see Filed)     |
| assigned_vm:NA corpus size  | 359 docs / 1295 todos | 376 docs / 1317 todos | +17 docs / +22 todos | ROUTE — `/na-eligibility-audit` scope (see Filed)                       |

## Flips verified

(appended as confirmed)

## Contradictions

(appended as confirmed)

## Doc-drift

(appended as confirmed)

## Hygiene fixes

(appended as applied)

## Filed

(appended as filed)

## Archive candidates (operator review)

(appended as archived / could-not-archive)

## Refuted (dropped by verify)

(appended as refuted)

## Coverage (hunters / batches / docs)

(appended at STEP 7)

## Plans not reached

(appended at STEP 7 if applicable)
