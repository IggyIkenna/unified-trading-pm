---
doc_type: issue
title: "plan_reconciler daily deep reconciliation — defi tranche run findings (2026-08-07)"
summary:
  "Run-findings doc + progress journal for plan_reconciler dispatch agt-a2268a, sharded to the defi tranche per the
  2026-08-06 operator ruling on sharded/weekly cadence. Scope: 107 docs under plans/active + plans/active/issues +
  plans/epics carrying asset_group or parent_epic containing 'defi' (Phase-0 inventory: 3.87MB, 45/107 in the 12h grace
  window). Fans out read-only hunter batches, adversarially verifies every candidate, auto-fixes the verified-easy,
  routes the hard ones. Updated incrementally as the run progresses."
status: open
nature: issue
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [role, plan_reconciler, reconciliation, plan-hygiene, defi, sharded-run]
related: []
created: 2026-08-07
author: plan_reconciler
source: agt-a2268a
locked_by: plan_reconciler-agt-a2268a
parent_epic: plan_hygiene_master
priority: P1
assigned_vm: NA
resolved_by:
---

# plan_reconciler — defi tranche run findings (2026-08-07, dispatch agt-a2268a)

> Persistent-until-resolved run doc. `TRANCHE=defi`. Sections below are appended as the run progresses; see Coverage for
> hunter/batch/doc counts and Plans not reached for anything the run could not get to.

## Phase-0 inventory summary

- Corpus scope: `plans/active/**` + `plans/active/issues/**` + `plans/epics/**` where `asset_group` or `parent_epic`
  contains `defi` (line-based frontmatter parse, scratch/audit subdirs excluded).
- 107 docs, 3,873,041 bytes total, avg 36.2 KB/doc.
- 45/107 (42%) inside the 12h grace window (newest git change <12h old) — READ-ONLY context this run, never written.
- Corpus-wide mechanical hygiene sweep (`run_hygiene_sweep.sh --ci`, whole corpus, not defi-filtered): 4 hard failures —
  reference-path-convention (83 format/92 existence, both over ratchet baseline), AG-closeout-linkage (77 orphans,
  baseline 69), terminal-status-archived (4, baseline 0 — none defi-tagged), archive-candidates (10, baseline 0 — 1
  defi-tagged: `defi_catalog_dp_catalog_001_shrink_blocked_2026_08_02.md`).
- Defi-tranche subset of the AG-closeout-linkage orphans: 9 issue docs (see Coverage / hunter batch assignments below)
  with `asset_group=[defi]` but no graph/mention path to `defi_consolidated_closeout_2026_07_18.md` or a satellite
  dispatch batch.

## Flips verified

_(populated in STEP 5 from STEP-4 HARD-confirmed candidates)_

## Contradictions

_(populated in STEP 5)_

## Doc-drift

_(populated in STEP 5/6 — plan↔codex drift; codex edits require an explicit operator ruling before any agent applies
them)_

## Hygiene fixes

_(populated in STEP 5)_

## Filed

_(STEP 6 — durable todos for anything routed)_

## Archive candidates (operator review)

_(STEP 5f)_

## Refuted (dropped by verify)

_(STEP 4)_

## Coverage (hunters / batches / docs)

- Phase-0 inventory: 107 docs / 3,873,041 bytes, partitioned into 8 hunter batches (greedy bin-pack, ~484 KB/batch
  target) — see hunter dispatch below for the exact file lists.
- Hunters dispatched: _(filled in as STEP 3 launches)_

## Plans not reached

_(if the run runs low on context before covering every confirmed item)_
