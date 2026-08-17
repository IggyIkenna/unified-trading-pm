---
doc_type: issue
title: >-
  cefi-aster- launcher-family hit the 2/day RB-INFRA-RELAUNCH dispatch budget — cefi-aster-2023-20260816-030139
  preempted and left un-relaunched by design; operator decision needed on whether the fleet size warrants a
  per-launcher-family budget increase
summary: >-
  DP-VM-008 escalation agt-648f49 (dispatched by `deployment_service.data_pipeline_monitors.escalation` with
  `wall_type=data_pipeline_failure`, authoring_slot=`dp-fleet-monitor`) reported VM
  `cefi-aster-2023-20260816-030139` (SPOT) as preempted, relaunchable via `launch-cefi-hl-aster-historical-backfill.sh`
  (no Tardis dependency). The dispatched worker's context explicitly read "DO NOT RELAUNCH...
  launcher-family cefi-aster- already hit 2/2 relaunch dispatches today (RB-INFRA-RELAUNCH bound)" — the same
  `escalation_dedup.check_relaunch_dispatch_budget` mechanism (`_MAX_RELAUNCH_DISPATCHES_PER_DAY = 2`,
  2026-08-10 fix) already documented for the `cefi-extended-` launcher-family in
  `cefi_extended_starknet_relaunch_dispatch_budget_hit_2026_08_16.md`. Live-verified (2026-08-16):
  `gcloud compute instances list --filter="name~'^cefi-aster-'"` returns **304 RUNNING SPOT instances**, and
  `cefi-aster-2023-20260816-030139` no longer exists in the fleet (confirmed gone, zero rows on an exact-name
  filter). No existing open issue doc covers this specific VM, launcher-family, or today's date — filing fresh per
  the runbook's "check for an existing open issue doc and page the operator instead of relaunching again"
  instruction (`/codex/15-runbooks/incidents/rb_infra_relaunch.md`). This is NOT a code bug — the budget enforced
  exactly as designed — but a genuinely enormous concurrently-preempting SPOT fleet (304 live instances, one
  launcher-family prefix — over 8x the 37-instance `cefi-extended-` case that surfaced the same trade-off the same
  day) can legitimately generate far more than 2 DISTINCT preemptions per calendar day, at which point almost every
  preemption that day goes un-relaunched until the day rolls over. That trade-off (slower shard-completion progress
  for `cefi-aster-2023-*` vs. the storm-prevention the budget was built for) is an operator judgment call, not
  something this worker should decide unilaterally.
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
    /plans/archive/issues/cefi_extended_starknet_relaunch_dispatch_budget_hit_2026_08_16.md,
    /plans/active/issues/mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-16"
author: unknown
priority: P2
parent_epic: observability_master
source:
  "DP-VM-008 escalation agt-648f49 dispatched via escalate-to-orchestrator (wall_type=data_pipeline_failure), handed
  to the data_pipeline_failure worker (slot 16) per the RB-INFRA-RELAUNCH bound instruction: check for an existing
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

# cefi-aster- launcher-family hit its 2/day RB-INFRA-RELAUNCH dispatch budget — VM left un-relaunched by design

> **📦 ARCHIVED 2026-08-17 — option B implemented, closed.** `deployment-service@2058bab339` implemented the
> `(launcher-family, shard-year)` finer-grouping-key mechanism per the operator's option-B ruling (see the Todos and
> Progress Log below). Closed together with `/plans/archive/issues/cefi_extended_starknet_relaunch_dispatch_budget_hit_2026_08_16.md`
> against the same commit.

> **🟢 RESOLVED 2026-08-16 (second pass, this session) — banner lifted.** The 304-VM `cefi-aster-` duplicate fleet
> this banner warned about has been cleaned up (513 duplicate VMs fleet-wide across both `cefi-aster-*` and
> `cefi-hyperliquid-*` terminated, 8 keepers — one per venue x year-shard — remain, repopulation-checked clean). See
> `plans/active/issues/hyperliquid_backfill_runaway_duplicate_launch_billing_waste_2026_08_16.md`'s Progress Log for
> full evidence. A separate latent gap found during that cleanup (`launch-cefi-hl-aster-historical-backfill.sh` never
> called `lc_write_launch_params`, so a SPOT-preemption relaunch would previously have blindly fanned out to all
> venues x all years) was also fixed (deployment-service@8c2a1da87e) — a future relaunch dispatch for this
> launcher-family is expected to be correctly single-shard-scoped now, not the launcher's bare full-fleet default.

## What I found

- Escalation `agt-648f49` (DP-VM-008, INFO severity) reported SPOT VM `cefi-aster-2023-20260816-030139` preempted,
  relaunchable via `launch-cefi-hl-aster-historical-backfill.sh` (no Tardis dependency). `escalation.py` generated a
  "DO NOT RELAUNCH" context (not a "RELAUNCH vm=..." instruction) because
  `escalation_dedup.check_relaunch_dispatch_budget(vm_name="cefi-aster-2023-20260816-030139")` returned
  `bounded=True`: the `cefi-aster-` launcher-family had already had `_MAX_RELAUNCH_DISPATCHES_PER_DAY = 2` DISTINCT
  VMs dispatched for relaunch today.
- Live-verified via `gcloud compute instances list --filter="name~'^cefi-aster-'"`: **304 RUNNING SPOT instances**
  under the `cefi-aster-2023-*` shard, all recently launched (creation timestamps clustered 2026-08-15T19:01Z
  through 2026-08-16T09:15Z, i.e. the last ~14h). `gcloud compute instances list
  --filter="name='cefi-aster-2023-20260816-030139'"` returns **zero rows** — the preempted VM is confirmed gone, no
  automated relaunch occurred, and the runbook's own "check for an already-running replacement under a fresh name"
  guidance (`rb_infra_relaunch.md` § "Bounds + safety") does not apply here — the budget block is
  launcher-family-wide, not vm_name-specific, so a fresh-name replacement for this exact shard would only appear if
  a human (or a future, budget-reset day) relaunches it.
- Checked the full `plans/active/issues/` + `plans/active/` corpus for `cefi-aster-2023-20260816-030139`,
  `cefi-aster-`, and escalation id `agt-648f49` — no existing open issue doc covers this specific
  VM/launcher-family/date combination. (`cefi_hl_aster_vm_resource_downsize_2026_08_10.md` and
  `cefi_hl_aster_batch_data_gaps_2026_06_22.md` are different, unrelated `hl-aster` topics — resource sizing and a
  June data-gap finding, not this relaunch-budget class; not duplicates.)

## Why it matters

This is NOT a bug — `check_relaunch_dispatch_budget` (added 2026-08-10 specifically to bound the
`features-sports-sports-*` 19-VM storm) worked exactly as designed: it stopped a further automated relaunch dispatch
and told the worker to escalate to a human instead of blindly retrying. But the `cefi-aster-` prefix currently
covers a **304-instance concurrently-running SPOT fleet** — over 8x the 37-instance `cefi-extended-starknet-*` fleet
that surfaced this exact same trade-off earlier the same day
(`cefi_extended_starknet_relaunch_dispatch_budget_hit_2026_08_16.md`). A fleet this large can legitimately produce
far more than 2 DISTINCT preemptions in a single calendar day purely from normal SPOT reclaim variance, at which
point almost every further preemption that day is left un-relaunched until the UTC day rolls over. That is the same
real trade-off between (a) the storm-prevention the budget exists for and (b) slower completion progress for large
sharded fleets under one launcher-family prefix — now observed twice, independently, on the same day, across two
different launcher-families (`cefi-extended-`, `cefi-aster-`) — worth an operator decision on whether the budget
should scale with concurrent fleet size (or move to a per-(launcher-family, shard-year) budget instead of
per-launcher-family), or whether this specific gap (this one `2023-20260816-030139` shard) should just be manually
relaunched now.

## Recommended decision

- **A**: Leave the budget as-is (global `_MAX_RELAUNCH_DISPATCHES_PER_DAY = 2` per launcher-family) — accept that
  large sharded fleets like `cefi-aster-2023-*` occasionally leave a preempted shard un-relaunched until the next
  UTC day; no code change needed, this specific gap self-heals on its own next preemption-driven dispatch once the
  day rolls over (or can be manually relaunched now if the operator wants it sooner).
- **B**: Scale the relaunch-dispatch budget by concurrent same-prefix fleet size (or move to a finer
  `(launcher-family, shard-year)` grouping key) so a genuinely large legitimate fleet doesn't get treated the same
  as a small one where 2 preemptions/day is already anomalous — a code change to `escalation_dedup.py`. This
  finding, seen twice in one day across two launcher-families, is stronger evidence for B than the first occurrence
  alone was.
- **My recommendation**: **A** for now, same rationale as the `cefi-extended-` sibling finding — the budget's
  storm-prevention purpose is more valuable than the marginal shard-completion delay for one aster shard-year, and
  a scaling scheme (B) risks reintroducing exactly the kind of storm the 2026-08-10 fix closed if sized wrong. But
  flagging that TWO independent same-day occurrences across two large SPOT fleets (37 and 304 instances) makes this
  a recurring-pattern signal, not a one-off — worth the operator weighing B if a third occurrence shows up. Flagging
  for operator awareness rather than unilaterally deciding, per `rb_infra_relaunch.md`'s explicit "page the
  operator" instruction — this is a judgment call about acceptable trade-offs, not a determinable-by-worker-alone
  outcome.

## What I did NOT do

- Did not relaunch `cefi-aster-2023-20260816-030139` — the bound explicitly says not to, and the runbook's own
  carve-out (root-cause-diagnosed relaunch with a shipped fix) doesn't apply: there is no bug here to fix, so no
  "genuinely new information" justifies bypassing the budget.
- Did not change `_MAX_RELAUNCH_DISPATCHES_PER_DAY` or any budget logic — that's option B above, an operator call.

## Todos

- [x] ✅ **RULED 2026-08-16 (operator, na-eligibility-audit follow-up): option B — scale the relaunch-dispatch
      budget by concurrent same-prefix fleet size** (or move to a finer `(launcher-family, shard-year)` grouping key,
      implementer's call which mechanism) in `escalation_dedup.py`. Same ruling applies to the sibling same-day
      occurrence `cefi_extended_starknet_relaunch_dispatch_budget_hit_2026_08_16.md` — do not implement this twice,
      fix it once in the shared `escalation_dedup.py` logic and close both docs against the same commit. **Repo
      correction: `escalation_dedup.py` lives in `deployment-service`, not `agent-orchestrator` as originally
      written** — `deployment-service@2058bab339`.

      Implemented the finer `(launcher-family, shard-year)` grouping-key mechanism, not fleet-size scaling —
      deliberately, since the PAUSE below flagged that the 304-instance `cefi-aster-` count was inflated by an
      unrelated duplicate-launch bug (now cleaned up per
      `plans/active/issues/hyperliquid_backfill_runaway_duplicate_launch_billing_waste_2026_08_16.md`'s Progress
      Log). The shard-year grouping key needs no live GCE fleet-size read at all, so it sidesteps that concern
      entirely: `_shard_group_key()` pulls the bare 4-digit shard-year segment out of `vm_name` (e.g.
      `cefi-aster-2023-20260816-030139` -> `"2023"`) and folds it into the day-partition budget key alongside the
      launcher-family prefix, so `cefi-aster-2023-*` and `cefi-aster-2024-*` now bound independently instead of
      sharing one flat per-launcher-family ≤2/day cap. A launcher-family whose VM names carry no shard-year segment
      falls back to today's unchanged flat grouping. See `deployment-service/deployment_service/data_pipeline_
      monitors/escalation_dedup.py`'s module comment above `_RELAUNCH_DISPATCH_STATE_ROOT` for the full rationale.
- [x] ✅ **N/A — option A (leave as-is) was not chosen**, so no manual relaunch is needed; the shard gap will be
      picked up once the scaled budget (todo above) lands.

## Progress Log

- 2026-08-16 (slot 16, data_pipeline_failure escalation agt-648f49): Received escalation for DP-VM-008
  `cefi-aster-2023-20260816-030139` preempted, `cefi-aster-` family already at 2/2 relaunch dispatches today.
  Checked for an existing issue doc naming this VM/launcher-family/date — none found (grepped
  `plans/active/issues/*.md` for the VM name, `cefi-aster-`, and the escalation id; found only unrelated
  `hl-aster` docs on different topics, and the same-day sibling `cefi-extended-` finding covering the identical
  budget mechanism on a different launcher-family). Confirmed via `gcloud compute instances list` the exact VM is
  no longer in the live fleet (0 rows) and the `cefi-aster-` family has 304 concurrently RUNNING instances. Per the
  runbook's explicit instruction, did not relaunch. Filed this issue doc and is paging the operator via `/blocked`.
- 2026-08-17 (slot 23, backend_engineer, AO task `cefi_aster_relaunch_dispatch_budget_hit-c3b611e212f2`): Implemented
  the operator's option-B ruling as the `(launcher-family, shard-year)` finer-grouping-key mechanism (not fleet-size
  scaling) in `escalation_dedup.py` — sidesteps the PAUSE banner's concern entirely since it reads no live GCE
  fleet-size at all, so the (now-resolved, per the linked hyperliquid duplicate-cleanup doc) inflated-count risk
  never applied to this mechanism. Added `_shard_group_key()` + wired it into `check_relaunch_dispatch_budget()`'s
  day-partition key; added unit coverage
  (`test_shard_group_key_extracts_bare_four_digit_year_after_prefix`,
  `test_shard_group_key_falls_back_to_bare_prefix_when_no_year_segment`,
  `test_check_relaunch_dispatch_budget_scopes_independently_per_shard_year`) confirming two DISTINCT shard-years
  under the identical `cefi-aster-` prefix now budget independently. Full `quality-gates.sh` green (3443 passed, 1
  pre-existing unrelated flaky timing test confirmed non-reproducing on re-run) and shipped via quickmerge:
  `deployment-service@2058bab339`. Closes this doc and the sibling
  `cefi_extended_starknet_relaunch_dispatch_budget_hit_2026_08_16.md` against the same commit per the todo's own
  instruction. `archive_exempt: true` set on THIS commit only (transitional — cross-repo flip discipline requires the
  checkbox-flip commit to land at the still-active path BEFORE any `git mv` archival, per
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`'s "never combine flip + git mv in one commit,
  cross-repo" rule); a follow-up commit in this same turn removes the exemption and archives this doc properly.
