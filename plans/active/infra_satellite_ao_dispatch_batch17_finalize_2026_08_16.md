---
doc_type: plan
title: infrastructure satellite AO batch 17 — finalize
summary: >-
  Gated closeout for infra_satellite_ao_dispatch_batch17_2026_08_16.md — machine-held via depends_on + gate_on_depends
  until every todo in that batch is done. Reconciles the batch's OPERATOR/REVIEW rulings and migration-group evidence
  back into the archived source issue doc, checks whether the SPOT-tier / metadata-from-file-tier follow-up work named
  in batch 17's own `## Deferred` section is now ready to draft (its gating OPERATOR todos resolved), and runs the
  standard 6-step archival ritual on the batch plan itself once done.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [infrastructure, ao-dispatch, satellite-batch, close-out, finalize]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch17_2026_08_16.md,
    /plans/archive/2026_08/issues/vm_launcher_setup_script_freshness_gap_2026_07_31.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-20"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.5
assigned_role: review
effort: low
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [infra_satellite_ao_dispatch_batch17_2026_08_16]
gate_on_depends: true
sequential: true
context_scope: [/plans/active/infra_satellite_ao_dispatch_batch17_2026_08_16.md, /codex/12-agent-workflow/plan-completion-and-archival-discipline.md, /codex/12-agent-workflow/commit-push-flip-rule.md, /codex/05-infrastructure/vm-launcher-runbook.md]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored in
  the same turn as batch 17, 2026-08-16 (slot 9, infra).
---

# infrastructure satellite AO batch 17 — finalize

> **Machine-gated on `/plans/active/infra_satellite_ao_dispatch_batch17_2026_08_16.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until every todo in that batch is `done`.

## Todos

- [ ] [REVIEW] P2. For each of batch 17's `[OPERATOR]`/`[REVIEW]` todos (SPOT-provisioning fork, `--metadata-from-file`
      fork, `--boot-disk-type` fork), confirm the ruling is recorded (either in the todo's own text or the batch plan's
      Progress Log) and reconcile it into
      `/plans/archive/2026_08/issues/vm_launcher_setup_script_freshness_gap_2026_07_31.md`'s Progress Log — that doc is
      now archived/resolved, so do not reopen it; append a dated Progress Log entry there summarizing the final
      resolution of tiers (2)/(3)/the SPOT gap, citing batch 17's commit(s). Done when: the archived issue doc's
      Progress Log reflects the terminal state of all three forks.
- [ ] [REVIEW] P2. Check whether the SPOT-provisioning and/or `--metadata-from-file` OPERATOR rulings from batch 17
      unblock the deferred migration work named in that plan's `## Deferred` section (79 SPOT launchers, 47
      metadata-from-file launchers). If either is now unblocked, draft the follow-up
      `infra_satellite_ao_dispatch_batch18_<date>.md` (same disjoint-~15-file-group pattern as batch 17's groups A/B/C)
      covering that tier — do not leave a resolved design fork with no drafted follow-up plan. If a ruling excluded a
      tier from migration entirely (the "carve-out" option), no follow-up plan is needed for that tier — record the
      carve-out in the runbook's Known Issues instead. Done when: either a batch-18 plan exists for each unblocked tier,
      or a documented carve-out exists for each excluded tier.
- [ ] [REVIEW] P2. Once `infra_satellite_ao_dispatch_batch17_2026_08_16.md` itself has zero open todos, run the standard
      6-step archival ritual on it (dated archive folder, banner, corpus-wide referrer-path fixup — including this
      finalize plan's own `related:` entry and `/codex/05-infrastructure/vm-launcher-runbook.md`'s Known Issues
      pointer), then archive this finalize plan too. Done when: both plans are under `plans/archive/`, and
      `regenerate_active_plan_inventory.py` reports zero orphan referrers to either.

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
