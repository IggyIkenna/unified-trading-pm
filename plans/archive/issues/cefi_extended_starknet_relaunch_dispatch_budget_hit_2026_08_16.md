---
doc_type: issue
title: >-
  cefi-extended- launcher-family hit the 2/day RB-INFRA-RELAUNCH dispatch budget — cefi-extended-starknet-2026-20260816-040430
  preempted and left un-relaunched by design; operator decision needed on whether the fleet size warrants a
  per-launcher-family budget increase
summary: >-
  DP-VM-008 escalation agt-213940 (dispatched by `deployment_service.data_pipeline_monitors.escalation` with
  `wall_type=data_pipeline_failure`, authoring_slot=`dp-fleet-monitor`) reported VM
  `cefi-extended-starknet-2026-20260816-040430` (SPOT) as preempted. `escalation.py`'s
  `escalation_dedup.check_relaunch_dispatch_budget` found the `cefi-extended-` launcher-family had already had 2
  DISTINCT VMs dispatched for relaunch today (`_MAX_RELAUNCH_DISPATCHES_PER_DAY = 2`,
  `escalation_dedup.py`), so the dispatched worker's context correctly read "DO NOT RELAUNCH... (RB-INFRA-RELAUNCH
  bound)" instead of a relaunch instruction — this is the intended behavior of the 2026-08-10 fix
  (`escalation_dedup.check_relaunch_dispatch_budget` docstring cites the 19-VM `features-sports-sports-*` storm it was
  built to bound). Live-verified (2026-08-16): `gcloud compute instances list --filter="name~'^cefi-extended-'"`
  returns 37 RUNNING SPOT instances across the starknet 2024/2025/2026 shard years, and
  `cefi-extended-starknet-2026-20260816-040430` no longer exists in the fleet (confirmed gone, not just renamed —
  no matching instance by exact name). No existing open issue doc covers this specific VM, launcher-family, or
  today's date — filing fresh per the runbook's "check for an existing open issue doc and page the operator instead
  of relaunching again" instruction (`/codex/15-runbooks/incidents/rb_infra_relaunch.md`). This is NOT a code bug —
  the budget enforced exactly as designed — but a genuinely large concurrently-preempting SPOT fleet (37 live
  instances, one launcher-family prefix) can legitimately generate more than 2 DISTINCT preemptions in a single
  calendar day, at which point every further preemption that day goes un-relaunched until the day rolls over. That
  trade-off (slower shard-completion progress for `cefi-extended-starknet-*` vs. the storm-prevention the budget was
  built for) is an operator judgment call, not something this worker should decide unilaterally.
status: resolved
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [cefi, vm, preemption, spot, relaunch-budget, rb-infra-relaunch, dp-vm-008, alerting, operator-decision]
related:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /plans/active/issues/mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-16"
author: unknown
priority: P2
parent_epic: observability_master
source:
  "DP-VM-008 escalation agt-213940 dispatched via escalate-to-orchestrator (wall_type=data_pipeline_failure), handed
  to the data_pipeline_failure worker (slot 19) per the RB-INFRA-RELAUNCH bound instruction: check for an existing
  open issue doc and page the operator instead of relaunching again."
assigned_vm: planning
execution_scope: orchestrator-agent
effort: max
estimate_class: research
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.24
assigned_role: data_engineering
drift_direction: none
depends_on: []
resolved_by: deployment-service@2058bab339
locked_by:
context_scope:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    deployment-service/deployment_service/data_pipeline_monitors/escalation.py,
    deployment-service/deployment_service/data_pipeline_monitors/escalation_dedup.py,
    deployment-service/deployment_service/vm_prefix_registry.py,
  ]
---

# cefi-extended- launcher-family hit its 2/day RB-INFRA-RELAUNCH dispatch budget — VM left un-relaunched by design

> **📦 ARCHIVED 2026-08-17 — option B implemented, closed.** `deployment-service@2058bab339` implemented the
> `(launcher-family, shard-year)` finer-grouping-key mechanism per the operator's option-B ruling (see the Progress
> Log below). Closed together with
> `/plans/archive/issues/cefi_aster_relaunch_dispatch_budget_hit_2026_08_16.md` against the same commit.

## What I found

- Escalation `agt-213940` (DP-VM-008, INFO severity) reported SPOT VM `cefi-extended-starknet-2026-20260816-040430`
  preempted. `escalation.py` generated a "DO NOT RELAUNCH" context (not a "RELAUNCH vm=..." instruction) because
  `escalation_dedup.check_relaunch_dispatch_budget(vm_name="cefi-extended-starknet-2026-20260816-040430")` returned
  `bounded=True`: the `cefi-extended-` launcher-family (longest-prefix match in `VM_PREFIX_TO_BUCKET`,
  `vm_prefix_registry.py:122`) had already had `_MAX_RELAUNCH_DISPATCHES_PER_DAY = 2` DISTINCT VMs dispatched for
  relaunch today.
- Live-verified via `gcloud compute instances list --filter="name~'^cefi-extended-'"`: **37 RUNNING SPOT
  instances** across `cefi-extended-starknet-{2024,2025,2026}-*` shard-years, all launched within the last ~24h
  (creation timestamps 2026-08-15T19:01–22:04Z). `gcloud compute instances list --filter="name='cefi-extended-starknet-2026-20260816-040430'"`
  returns **zero rows** — the preempted VM is confirmed gone, no automated relaunch occurred, and the runbook's own
  "check for an already-running replacement under a fresh name" guidance
  (`rb_infra_relaunch.md` § "Bounds + safety") does not apply here — the budget block is launcher-family-wide, not
  vm_name-specific, so a fresh-name replacement for this exact shard would only appear if a human (or a future,
  budget-reset day) relaunches it.
- Checked the full `plans/active/issues/` + `plans/active/` corpus for `cefi-extended-starknet-2026-20260816-040430`,
  `cefi-extended-`, `DP-VM-008`, and escalation id `agt-213940` — no existing open issue doc covers this specific
  VM/launcher-family/date combination. (`cefi_fwd_vm_preempted_false_positive_standard_provisioning_2026_08_06.md` is
  a different, already-closed false-positive class on a different launcher-family; not a duplicate.)

## Why it matters

This is NOT a bug — `check_relaunch_dispatch_budget` (added 2026-08-10 specifically to bound the
`features-sports-sports-*` 19-VM storm, see `escalation_dedup.py`'s module comment) worked exactly as designed:
it stopped a further automated relaunch dispatch and told the worker to escalate to a human instead of blindly
retrying. But the `cefi-extended-` prefix currently covers a **37-instance concurrently-running SPOT fleet** spanning
three shard-years (2024/2025/2026) of one instrument (`starknet`) — a fleet this large can legitimately produce more
than 2 DISTINCT preemptions in a single calendar day purely from normal SPOT reclaim variance, at which point every
further preemption that day is left un-relaunched until the UTC day rolls over. That is a real trade-off between
(a) the storm-prevention the budget exists for and (b) slower completion progress for large sharded fleets under one
launcher-family prefix — worth an operator decision on whether `cefi-extended-`'s effective budget should scale with
concurrent fleet size (or move to a per-(launcher-family, shard-year) budget instead of per-launcher-family), or
whether today's specific gap (this one `2026-20260816-040430` shard) should just be manually relaunched now.

## Recommended decision

- **A**: Leave the budget as-is (global `_MAX_RELAUNCH_DISPATCHES_PER_DAY = 2` per launcher-family) — accept that
  large sharded fleets like `cefi-extended-starknet-*` occasionally leave a preempted shard un-relaunched until the
  next UTC day; no code change needed, this specific gap self-heals on its own next preemption-driven dispatch once
  the day rolls over (or can be manually relaunched now if the operator wants it sooner).
- **B**: Scale the relaunch-dispatch budget by concurrent same-prefix fleet size (or move to a finer
  `(launcher-family, shard-year)` grouping key) so a genuinely large legitimate fleet doesn't get treated the same as
  a small one where 2 preemptions/day is already anomalous — a code change to `escalation_dedup.py`.
- **My recommendation**: **A** for now — the budget's storm-prevention purpose (stopping a mass-relaunch fan-out) is
  more valuable than the marginal shard-completion delay for one starknet shard-year, and a scaling scheme (B) risks
  reintroducing exactly the kind of storm the 2026-08-10 fix closed if sized wrong. Flagging for operator awareness
  rather than unilaterally deciding, per `rb_infra_relaunch.md`'s explicit "page the operator" instruction — this is
  a judgment call about acceptable trade-offs, not a determinable-by-worker-alone outcome.

## What I did NOT do

- Did not relaunch `cefi-extended-starknet-2026-20260816-040430` — the bound explicitly says not to, and the runbook's
  own carve-out (root-cause-diagnosed relaunch with a shipped fix) doesn't apply: there is no bug here to fix, so no
  "genuinely new information" justifies bypassing the budget.
- Did not change `_MAX_RELAUNCH_DISPATCHES_PER_DAY` or any budget logic — that's option B above, an operator call.

## Update 2026-08-16 (second occurrence, same day) — escalation agt-dc9224

- A second, distinct DP-VM-008 escalation (`agt-dc9224`, dispatched by `deployment_service.data_pipeline_monitors.escalation`
  with `wall_type=data_pipeline_failure`, `authoring_slot=dp-fleet-monitor`) reported a DIFFERENT SPOT VM,
  `cefi-extended-starknet-2025-20260816-020053`, preempted — again with a "DO NOT RELAUNCH... cefi-extended- already hit
  2/2 relaunch dispatches today (RB-INFRA-RELAUNCH bound)" instruction, same launcher-family/day budget bound documented
  above.
- Per `rb_infra_relaunch.md`'s "check for an existing open issue doc and page the operator instead of relaunching
  again" instruction: this doc already covers the exact launcher-family (`cefi-extended-`) + date (2026-08-16) + root
  cause (2/day `_MAX_RELAUNCH_DISPATCHES_PER_DAY` bound) — filing a second duplicate issue doc would fragment the same
  operator decision across two docs, so appending here instead (per the workspace's append-not-overwrite rule for
  shared docs) rather than creating a new file.
- Live-verified (2026-08-16): `gcloud compute instances list --filter="name~'^cefi-extended-starknet'"` still shows 37
  RUNNING instances across the 2024/2025/2026 shard-years; `gcloud compute instances list
  --filter="name='cefi-extended-starknet-2025-20260816-020053'"` returns **zero rows** — this VM is confirmed gone, no
  automated relaunch occurred (expected — the budget is launcher-family-wide), and no fresh-name replacement for this
  specific shard is visible in the fleet.
- No code fix applies here either (same root cause as the first occurrence — the budget worked exactly as designed).
  This second occurrence is additional evidence for the operator-decision trade-off above: the `cefi-extended-`
  launcher-family is now confirmed to have hit its 2/day budget from at least 2 DISTINCT preemption events on
  2026-08-16 alone, reinforcing that a 37-instance concurrently-running fleet under one launcher-family prefix can
  legitimately exceed a flat 2/day bound. Does not change the recommendation (**A**, leave as-is) — just strengthens
  the case for the operator to weigh it.
- Did not relaunch `cefi-extended-starknet-2025-20260816-020053`; did not change any budget logic; status stays `open`,
  pending the same A/B operator decision above.
- **2026-08-16 (na-eligibility-audit follow-up, operator ruling)**: option B ruled (scale relaunch-dispatch budget by
  concurrent fleet size, or a finer grouping key) — same fix as `cefi_aster_relaunch_dispatch_budget_hit_2026_08_16.md`,
  do not implement twice, close both against the same `escalation_dedup.py` commit.
- **2026-08-17 (slot 23, backend_engineer, AO task `cefi_aster_relaunch_dispatch_budget_hit-c3b611e212f2`) — RESOLVED,
  closing per the shared-commit instruction above.** Implemented option B as a `(launcher-family, shard-year)` finer
  grouping key (not fleet-size scaling) in
  `deployment-service/deployment_service/data_pipeline_monitors/escalation_dedup.py` — `_shard_group_key()` now folds
  the bare 4-digit shard-year segment parsed from `vm_name` (e.g. `cefi-extended-starknet-2026-...` -> `"2026"`) into
  the day-partition budget key alongside the launcher-family prefix, so `cefi-extended-starknet-2024-*`,
  `-2025-*`, and `-2026-*` now bound independently instead of sharing one flat ≤2/day cap across all three
  shard-years. Repo correction: this code lives in `deployment-service`, not `agent-orchestrator`. Full
  `quality-gates.sh` green (3443 passed; one pre-existing unrelated flaky VM-launcher timing test did not reproduce
  on re-run), shipped via quickmerge: `deployment-service@2058bab339`. Fixed once, closing both this doc and
  `cefi_aster_relaunch_dispatch_budget_hit_2026_08_16.md` against this same commit.
