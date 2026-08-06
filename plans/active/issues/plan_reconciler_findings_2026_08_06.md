---
doc_type: issue
title: plan_reconciler findings — 2026-08-06 (cefi tranche shard)
summary:
  Run-findings doc for plan_reconciler dispatch agt-bf8439 (cefi tranche). Fan-out DETECT + adversarial VERIFY over the
  cefi corpus; only CONFIRMED items acted on. Grace-window docs are read-only and reported.
status: open
nature: process
asset_group: [cefi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan_reconciler, findings, reconciliation, cefi]
related: [cefi_consolidated_closeout_2026_07_18.md]
created: 2026-08-06
author: plan_reconciler
source: agt-bf8439
parent_epic: cefi_master
priority: P2
assigned_vm: NA
locked_by: plan_reconciler
resolved_by:
---

# plan_reconciler findings — 2026-08-06 (cefi tranche shard)

> Sharded reconciliation run for the `cefi` tranche (dispatch `agt-bf8439`, slot 12). Working set = 93 cefi
> `asset_group` docs; 43 in the 12h grace window (read-only), 50 writable. Normative refs + codex in scope per shard.
> Every action below survived the STEP-4 adversarial verification; refuted candidates are logged under `## Refuted`.

## Run inventory

- Cefi corpus: 93 docs (41 plans/active + 52 plans/active/issues), 50 writable / 43 grace
- Grace set corpus-wide: 316 docs (heavily-worked corpus; touches through 2026-08-06 20:01 UTC)
- Hygiene sweep: 4 hard failures corpus-wide (reference-path ratchet 83v81 / 88v86, AG-closeout linkage 75v69,
  terminal-status-archived 3v0, archive-candidates ratchet); 0 archive candidates from the mechanical sweep
- Phase-0 candidates for this shard: 2 AG-closeout orphans, 3 todo-format docs, 1 delete/VM-launch soft-warn (grace), 3
  terminal-status violations (ALL grace)

## Flips verified

(pending STEP 4)

## Contradictions

(pending)

## Doc-drift

(pending)

## Hygiene fixes

(pending)

## Filed

(pending)

## Archive candidates (operator review)

(pending)

## Refuted (dropped by verify)

(pending)

## Coverage (hunters / batches / docs)

(pending)

## Plans not reached

(pending)
