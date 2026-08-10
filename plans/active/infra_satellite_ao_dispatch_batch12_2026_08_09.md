---
doc_type: plan
title: Infra satellite AO batch 12 — managed-by launcher label standardization (batch1's last cleared deferral)
summary: >-
  Twelfth AO-dispatch batch for the `infra` topic tranche. Single source: the one remaining CLEARED-but-unbatched item
  from `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s Deferred section (item 5, "`managed-by` launcher label
  standardization") — re-checked by that batch's own finalize plan
  (`infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md` todo 2, 2026-08-09) and confirmed CLEARED: both competing
  claims on the adjacent files (this batch's own PROGRESS.json launcher-lib rollout, and the Cloud-Run job terraform
  `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` touched) have shipped, so the collision risk that
  originally parked this item is gone. Drafted as batch1 archives so the item is not lost to archival. Low value on its
  own (the source doc's own text: `launched_by` already answers "who launched this" for most operator purposes) — P3,
  single bounded todo.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [infra, ao-dispatch, satellite-docs, batch-12, vm-launcher, labels]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch12_finalize_2026_08_09.md,
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: infra
effort: medium
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_2026_07_26.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  `infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md` todo 4 (archival of batch 1) — migrating batch 1's last
  cleared-but-unbatched Deferred item into a real home per the finalize plan's "nothing may be lost to archival" step.
---

# Infra satellite docs — AO dispatch batch 12

## Why this plan exists

`infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s Deferred item 5 parked `managed-by` launcher-label standardization
because it touched `deployment-service/scripts/vm/launch-*.sh` (adjacent to that batch's own in-flight PROGRESS.json
launcher-lib rollout) and Cloud-Run job terraform (which `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` was
also touching). Both competing claims have since shipped (re-verified by the finalize plan's todo 2, 2026-08-09),
clearing the collision. Live re-measurement (2026-08-09): `142/177` `launch-*.sh` scripts under
`deployment-service/scripts/vm/` set a `managed-by=deployment-service` GCE label; `35` do not.

## Conflict check (before drafting)

- Grepped every active + archived `infra_*batch*`/`*finalize*` doc and
  `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` for `managed-by.*launcher\|launcher label` — no other live
  claim on this delta.
- The PROGRESS.json launcher-lib rollout (batch 1) and the Cloud-Run terraform (cross-cutting batch1b) are both fully
  shipped/archived — no active edit in flight on either adjacent surface.

## Todos

- [ ] [INFRA] P3. **Standardize the `managed-by=deployment-service` GCE label across all
      `deployment-service/scripts/vm/launch-*.sh` launchers.** Live-measured 2026-08-09: 35 of 177 launchers omit the
      label (`grep -L 'managed-by=' scripts/vm/launch-*.sh` lists the exact set). Add the label to each missing
      launcher's `--labels=` gcloud invocation, following the existing `purpose=...,...,managed-by=deployment-service`
      convention already used by the 142 conformant launchers (see `launch-backfill-candle-manifest-vm.sh:181` for the
      reference shape). Done when: `grep -L 'managed-by=' scripts/vm/launch-*.sh` returns empty, and `quality-gates.sh`
      stays green (shell-script tests, if any, unaffected — this is a label-string addition only, no control-flow
      change). Source: `infra_satellite_ao_dispatch_batch1_2026_07_26.md` Deferred item 5. Repo: deployment-service.

## Operator approval gate

**This plan is `status: draft` — awaiting operator review.** Flip to `status: active` only after explicit approval (its
finalize twin is drafted alongside it, gated on this plan per the finalize-plan-coverage rule).

## Codex SSOTs (read before touching a todo)

- `/codex/05-infrastructure/vm-launcher-runbook.md` — launcher conventions
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — archival ritual the finalize plan runs
- `/plans/active/task_template.md` §4 — finalize-plan-coverage rule

## Progress Log

- **2026-08-09 (slot-31)** — Drafted while archiving `infra_satellite_ao_dispatch_batch1_2026_07_26.md`
  (`infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md` todo 4), to give batch 1's one remaining
  cleared-but-unbatched Deferred item (item 5) a real home before archival. Paired with
  `infra_satellite_ao_dispatch_batch12_finalize_2026_08_09.md` per the finalize-plan-coverage rule.
