---
doc_type: plan
title: infra satellite AO batch 2 — finalize
summary: >-
  Gated closeout for infra_satellite_ao_dispatch_batch2_2026_08_21.md — machine-held via depends_on +
  gate_on_depends until every todo in that batch is done. Reconciles each completed todo's evidence back into its
  TRUE source doc's checkbox across all 3 source docs, archives any source doc that reaches zero open
  infra-relevant todos as a result (with corpus-wide referrer updates so the archival doesn't break the
  broken-link gate), and runs the standard 6-step archival ritual on the batch plan itself.
status: draft
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [infra, ao-dispatch, satellite-batch, close-out, finalize]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch2_2026_08_21.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: review
effort: low
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [infra_satellite_ao_dispatch_batch2_2026_08_21]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/infra_satellite_ao_dispatch_batch2_2026_08_21.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/11-project-management/cross-reference-path-convention.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored
  in the same turn as its batch, 2026-08-21 ag-closeout-audit Phase 3 session.
---

# infra satellite AO batch 2 — finalize

> **Machine-gated on `/plans/active/infra_satellite_ao_dispatch_batch2_2026_08_21.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until every todo in that batch is `done`.

## Todos

- [ ] [REVIEW] P2. For every completed todo in `infra_satellite_ao_dispatch_batch2_2026_08_21.md`, reconcile the
      evidence back into its cited source doc's own checkbox — this batch has 3 distinct source docs
      (`deployment_service_client_broken_functions_2026_08_20.md` for todos 1-11,
      `agent_orchestrator_pytest_cov_silent_death_under_host_load_2026_08_20.md` for todos 12-13,
      `agent_orchestrator_qg_baseline_stale_cgroup_kill_2026_08_20.md` for todos 14-15). Find each matching item and
      either flip it `[x]` with a citation to this batch's commit, or add a note pointing at the batch todo that
      superseded it. Re-verify each cited commit sha is real (`git cat-file -t`), do not trust the batch's own
      checkbox alone. Done when: all 3 source docs touched by this batch have their corresponding items' checkbox
      state reconciled.
- [ ] [REVIEW] P2. For each source doc reconciled above, check whether it now has zero open todos. If fully zero,
      run the standard 6-step archival ritual (dated archive folder, exact-successor banner if applicable,
      corpus-wide referrer-path fixup — grep the WHOLE corpus for the old path, not just the docs this batch
      touched, since other docs may reference these too). Note:
      `deployment_service_client_broken_functions_2026_08_20.md` will likely reach zero (all 11 items are in this
      batch); the other two source docs each have a deliberately-NOT-extracted open item left behind (RSS-doubling
      investigation; host-level `--cov` death investigation) and will NOT be zero — do not archive those two.
      Done when: every source doc left with zero open todos is archived, and `run_hygiene_sweep.sh` reports no
      orphan referrers to any of them.
- [ ] [REVIEW] P2. Once `infra_satellite_ao_dispatch_batch2_2026_08_21.md` itself has zero open todos, run the
      standard 6-step archival ritual on it, then archive this finalize plan too. Done when: both are under
      `plans/archive/`, and `regenerate_active_plan_inventory.py` reports zero orphan referrers to either.

## Progress Log

- **2026-08-21 (ag-closeout-audit, infra tranche, Phase 3)**: authored alongside the batch.
