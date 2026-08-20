---
doc_type: plan
title: Finalize — DeFi satellite AO batch 18 close-out
summary: >-
  Gated finalize companion for defi_satellite_ao_dispatch_batch18_2026_08_19.md — re-verifies each of the 9 todos'
  reported findings against the source docs' own citations, folds any newly-confirmed result back into the 8
  originating docs, then archives both docs per plan-completion-and-archival-discipline once every todo is done.
status: active
nature: process
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, finalize, batch-18, ag-closeout-audit, archival]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch18_2026_08_19.md,
    /plans/active/issues/ag_closeout_audit_defi_parked_2026_08_19.md,
  ]
created: "2026-08-19"
last_updated: "2026-08-20"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.16
assigned_role: data_engineering
effort: low
thinking_tier: mechanical
depends_on: [defi_satellite_ao_dispatch_batch18_2026_08_19]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/defi_satellite_ao_dispatch_batch18_2026_08_19.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/issues/ag_closeout_audit_defi_parked_2026_08_19.md,
  ]
source: >-
  ag_closeout_auditor 2026-08-19 (dispatch agt-fa5ded, slot 28) — every AO-dispatched satellite batch needs a gated
  finalize companion (/plans/active/task_template.md §4).
drift_direction: advance-code
---

# Finalize — DeFi satellite AO batch 18 close-out

Machine-held (`gate_on_depends: true`) until every todo in `defi_satellite_ao_dispatch_batch18_2026_08_19.md` is done.
Do not start manually before then.

## Todos

- [ ] [REVIEW] P2. Re-verify all 9 of batch18's todos' reported findings independently (don't trust the batch doc's
      own checkbox alone) — for the two GCS/data-migration items (dex_swaps migration, test-bucket delete), confirm
      the five-part delete-safety proof was actually filed and passed, not just claimed; for the VM/job-verification
      items (blazestake OOM fix, Era-B G4 coupling), re-run the cited verification command rather than trusting the
      prior run's report; for the build items (MTDS chain-field collectors, Option B staking-return metric, Pendle
      scheduler wiring), confirm quality-gates.sh is actually green on every touched repo. Correct any mis-citation
      found in the batch doc itself. Fold whatever was actually found back into each of the 8 originating source
      docs. Done-when: all 9 todos independently re-verified with cited evidence, every source doc updated to reflect
      what was found.
- [ ] [DOC] P2. Once every batch18 todo + the REVIEW todo above are done: run the standard 6-step
      plan-completion-and-archival-discipline ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) on
      `defi_satellite_ao_dispatch_batch18_2026_08_19.md` and this finalize doc itself — archive both to
      `plans/archive/2026_08/`, fix every corpus referrer path. Done-when: `regenerate_active_plan_inventory.py`
      shows zero orphan referrers to the archived paths.

## Progress Log

- **2026-08-19 (ag_closeout_auditor, defi tranche, dispatch agt-fa5ded, slot 28)**: finalize plan authored alongside
  batch18's draft, per `task_template.md`'s finalize-plan-coverage rule.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
