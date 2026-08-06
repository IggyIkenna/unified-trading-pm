---
doc_type: issue
title: plan_reconciler findings — defi tranche — 2026-08-06
summary:
  Run-findings doc for the sharded daily plan-reconciler run (tranche=defi). Candidate register, verification results,
  applied fixes, routed items, coverage ledger.
status: open
created: "2026-08-06"
author: plan_reconciler
source: agt-24f4b0
nature: issue
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
parent_epic: defi_master
priority: P3
assigned_vm: NA
resolved_by: >-
asset_group: [defi]
tags: [plan-reconciler, run-findings, defi]
related: [defi_consolidated_closeout_2026_07_18]
locked_by: agt-24f4b0
---

# plan_reconciler run findings — defi tranche — 2026-08-06

Dispatch: `agt-24f4b0` · slot 7 · tranche `defi` · review branch `plan_reconciler/agt-24f4b0`

## Scope + inventory

- defi-tranche corpus (asset_group matching defi): **96 docs** = 28 active plans + 67 issue docs + 1 epic
  (`defi_master`)
- 12h GRACE SET (read-only this run): **45 docs** — heavily in-flight corpus (batch9/batch10 dispatches,
  hyperliquid→cefi migration, LST-rate work)
- WORKING SET (fixable): **51 docs** = 41 with open todos + 9 fully-done/zero-open candidates + 1 epic (41 open todos)
- Zero-checkbox docs in working set: `candle_feature_canonical_path_divergence_2026_07_20.md`,
  `defi_kamino_lending_venue_drift_live_data_verification_gap_2026_08_04.md`,
  `mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md`

## Flips verified

(append as confirmed)

## Contradictions

(append as confirmed)

## Doc-drift

(append as confirmed)

## Hygiene fixes

(append as applied)

## Filed

(append as filed)

## Archive candidates (operator review)

(append as confirmed)

## Refuted (dropped by verify)

(append as refuted)

## Coverage (hunters / batches / docs)

(append per hunter batch)

## Plans not reached

(append if any)

## Phase-5.9 ledger

- routed_to_operator: TBD
- parked_in_issue_doc: TBD
- agent_skips: TBD (enumerated below if any)
