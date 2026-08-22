---
doc_type: issue
title: >-
  tradfi-bf-cme-ohlcv-1m- launcher family hit the 2/day RB-INFRA-RELAUNCH dispatch budget —
  tradfi-bf-cme-ohlcv-1m-g02-6m-cl-2024-20260816-220540 preempted and left un-relaunched by design; operator decision
  needed, same trade-off as the same-day cefi-aster-/cefi-extended- occurrences
summary: >-
  DP-VM-008 escalation agt-ee0261 (dispatched by `deployment_service.data_pipeline_monitors.escalation` with
  `wall_type=data_pipeline_failure`, authoring_slot=`dp-fleet-monitor`) reported VM
  `tradfi-bf-cme-ohlcv-1m-g02-6m-cl-2024-20260816-220540` (SPOT) as preempted, relaunchable via
  `launch-tradfi-bf-cme-ohlcv-1m.sh` (no Tardis dependency). The dispatched worker's context explicitly read "DO NOT
  RELAUNCH... launcher-family tradfi-bf-cme-ohlcv-1m- already hit 2/2 relaunch dispatches today (RB-INFRA-RELAUNCH
  bound)" — the same `escalation_dedup.check_relaunch_dispatch_budget` mechanism
  (`_MAX_RELAUNCH_DISPATCHES_PER_DAY = 2`, 2026-08-10 fix) already documented today for the `cefi-extended-` and
  `cefi-aster-` launcher-families (`cefi_extended_starknet_relaunch_dispatch_budget_hit_2026_08_16.md`,
  `cefi_aster_relaunch_dispatch_budget_hit_2026_08_16.md`). Live-verified (2026-08-16, ~23:04 UTC):
  `gcloud compute instances list --filter="name~'^tradfi-bf-cme-ohlcv-1m'"` returns 36 RUNNING instances across
  launcher groups g01-g06 (years 2020-2026), all launched in a single wave ~15:02-15:14 PT the same afternoon — but
  `tradfi-bf-cme-ohlcv-1m-g02-6m-cl-2024-*` is conspicuously ABSENT from that wave (the family shows 2020, 2022,
  2023, 2025, 2026 shards for group g02-6m-cl, but not 2024), and an exact-name filter for the preempted VM returns
  zero rows — confirmed gone, not relaunched. This same launcher-family ALSO has two OPEN same-day DP-VM-001
  (exit_code=137 stall, a different alert class) issue docs already citing the identical "2/2 relaunch dispatches
  today" bound (`dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_exit137_stall_relaunch_bound_page_2026_08_16.md`,
  `dp_vm_001_tradfi_bf_cme_ohlcv_1m_btc_2020_exit137_stall_relaunch_bound_page_2026_08_16.md`) — this is now the
  THIRD distinct relaunch-blocked incident against the same launcher-family prefix today, across two different
  DP-* alert classes. No existing open issue doc covers this specific VM or the DP-VM-008 preemption class for this
  launcher-family — filing fresh per the runbook's "check for an existing open issue doc and page the operator
  instead of relaunching again" instruction (`/codex/15-runbooks/incidents/rb_infra_relaunch.md`). This is NOT a
  code bug — the budget enforced exactly as designed.
status: open
nature: issue
asset_group: [tradfi]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [tradfi, vm, preemption, spot, relaunch-budget, rb-infra-relaunch, dp-vm-008, alerting, operator-decision]
related:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /plans/archive/issues/cefi_extended_starknet_relaunch_dispatch_budget_hit_2026_08_16.md,
    /plans/archive/issues/cefi_aster_relaunch_dispatch_budget_hit_2026_08_16.md,
    /plans/archive/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_exit137_stall_relaunch_bound_page_2026_08_16.md,
    /plans/active/issues/dp_vm_001_tradfi_bf_cme_ohlcv_1m_btc_2020_exit137_stall_relaunch_bound_page_2026_08_16.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-16"
author: unknown
priority: P2
parent_epic: observability_master
source:
  "DP-VM-008 escalation agt-ee0261 dispatched via escalate-to-orchestrator (wall_type=data_pipeline_failure), handed
  to the data_pipeline_failure worker (slot 11) per the RB-INFRA-RELAUNCH bound instruction: check for an existing
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
resolved_by:
locked_by:
context_scope:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    deployment-service/deployment_service/data_pipeline_monitors/escalation.py,
    deployment-service/deployment_service/data_pipeline_monitors/escalation_dedup.py,
    deployment-service/deployment_service/vm_prefix_registry.py,
    deployment-service/scripts/vm/launch-tradfi-bf-cme-ohlcv-1m.sh,
  ]
---

# tradfi-bf-cme-ohlcv-1m- launcher family hit its 2/day RB-INFRA-RELAUNCH dispatch budget — VM left un-relaunched by design

## What I found

- Escalation `agt-ee0261` (DP-VM-008, INFO severity) reported SPOT VM
  `tradfi-bf-cme-ohlcv-1m-g02-6m-cl-2024-20260816-220540` preempted, relaunchable via
  `launch-tradfi-bf-cme-ohlcv-1m.sh` (no Tardis dependency). `escalation.py`'s
  `escalation_dedup.check_relaunch_dispatch_budget` found the `tradfi-bf-cme-ohlcv-1m-` launcher-family had already
  had 2 DISTINCT VMs dispatched for relaunch today (`_MAX_RELAUNCH_DISPATCHES_PER_DAY = 2`, `escalation_dedup.py`),
  so the dispatched worker's context correctly read "DO NOT RELAUNCH... (RB-INFRA-RELAUNCH bound)" instead of a
  relaunch instruction — the intended behavior of the 2026-08-10 fix.
- Live-verified (2026-08-16, ~23:04 UTC): `gcloud compute instances list --filter="name~'^tradfi-bf-cme-ohlcv-1m'"`
  returns 36 RUNNING instances across launcher groups g01-g06 (years 2020-2026), all launched in one wave between
  ~15:02 and ~15:14 PT the same afternoon. The `g02-6m-cl` group shows shards for 2020, 2022, 2023, 2025, and 2026 —
  but NOT 2024, matching exactly the preempted VM's shard token. An exact-name filter for
  `tradfi-bf-cme-ohlcv-1m-g02-6m-cl-2024-20260816-220540` returns zero rows — confirmed gone, not relaunched, and
  the `2024` shard for this group is not present anywhere in the current wave.
- Checked `plans/active/issues/` for the exact VM name and `DP-VM-008`+`tradfi-bf-cme-ohlcv-1m` — no existing open
  issue doc covers this specific VM, launcher-family, or the DP-VM-008 preemption class for this family today. Two
  same-family, same-day sibling docs DO exist, but for a DIFFERENT alert class (DP-VM-001, `exit_code=137`
  stall-induced kills, not SPOT preemption): `g01-6a-6l-2020-20260816-162556` and `btc-2020-20260816-180410`, both
  also citing the identical "2/2 relaunch dispatches today" bound language for this same launcher-family prefix.

## Why it matters

This is NOT a bug — `check_relaunch_dispatch_budget` worked exactly as designed: it stopped a further automated
relaunch dispatch and told the worker to escalate to a human instead of blindly retrying. But this is now the
**third** distinct relaunch-blocked incident against the `tradfi-bf-cme-ohlcv-1m-` prefix TODAY, across **two
different DP-\* alert classes** (DP-VM-001 exit137 stalls ×2, DP-VM-008 SPOT preemption ×1 here) — the same
cross-day/cross-shard pattern already flagged as worth operator attention in the `btc-2020` sibling doc, now also
crossing alert-class boundaries on the same launcher-family prefix. It also mirrors, same-day, the identical
per-launcher-family budget trade-off already surfaced twice for `cefi-extended-` (37 live instances) and
`cefi-aster-` (304 live instances, later found to include duplicate-launch pollution — see that doc's PAUSED
banner): a 36-instance concurrently-running SPOT fleet under one launcher-family prefix can legitimately generate
more than 2 DISTINCT preemptions in a single calendar day, at which point further preemptions that day go
un-relaunched until the day rolls over. Unlike the `cefi-aster-` case, this worker did NOT find evidence of a
duplicate-launch/billing-waste pattern here — the 36-instance count matches the expected shard cardinality (6
groups × up to 7 years each, single VM per shard), so this looks like genuine large-legitimate-fleet pressure, not
a repeat of the `cefi-aster-` pollution issue.

## Recommended decision

- **A**: Leave the budget as-is (global `_MAX_RELAUNCH_DISPATCHES_PER_DAY = 2` per launcher-family) — accept that
  `tradfi-bf-cme-ohlcv-1m-2024-g02-6m-cl` stays un-relaunched until the day rolls over (or manually relaunch this
  one shard now if the operator wants it sooner); no code change needed.
- **B**: Scale the relaunch-dispatch budget by concurrent same-prefix fleet size (or move to a finer
  `(launcher-family, shard-year)` grouping key) — the same option B already raised (and currently PAUSED pending
  the `cefi-aster-` duplicate-launch cleanup) in the `cefi-aster-`/`cefi-extended-` sibling docs. **Do not implement
  this separately** — if the operator chooses B, it should be fixed once in `escalation_dedup.py` and close all
  three same-day docs (this one + the two cefi siblings) against the same commit.
- **My recommendation**: **A** for now, same rationale as both cefi siblings — but this occurrence, being genuinely
  legitimate fleet pressure (no duplicate-launch pollution found here, unlike `cefi-aster-`), is cleaner evidence
  for B than either cefi case alone. Worth weighing once the `cefi-aster-` cleanup (referenced in that doc's
  PAUSED banner) lands and the operator re-evaluates B against real fleet sizes across all three launcher-families.

## What I did NOT do

- Did not relaunch `tradfi-bf-cme-ohlcv-1m-g02-6m-cl-2024-20260816-220540` — the bound explicitly says not to, and
  the runbook's root-cause-diagnosed carve-out doesn't apply (no bug here to fix).
- Did not change `_MAX_RELAUNCH_DISPATCHES_PER_DAY` or any budget logic — that's option B above, an operator call.
- Did not cross-check `run.log`/failure signatures against the two open DP-VM-001 sibling docs for this same
  family — those track a different alert class (stall/exit137) and their own root-cause todos already cover that.

## Todos

- [x] ✅ [OPERATOR] P2. Decide option A vs B (above) for the `tradfi-bf-cme-ohlcv-1m-` launcher-family's relaunch
      dispatch budget; if B, implement once in `escalation_dedup.py` (repo: agent-orchestrator) and close this doc
      plus `cefi_extended_starknet_relaunch_dispatch_budget_hit_2026_08_16.md` and
      `cefi_aster_relaunch_dispatch_budget_hit_2026_08_16.md` against the same commit — do not implement per-doc.
      **DONE** — option B ruled + shipped `deployment-service@2058bab339` (`_shard_group_key()`/`_SHARD_YEAR_RE`,
      scopes the relaunch-dispatch budget by (launcher-family, shard-year)), verified ancestor of
      `origin/live-defi-rollout`. The two cefi sibling docs cite this same commit and are archived. Its `Closes:`
      trailer names only the 2 cefi docs, not this one — but the fix is generic (not cefi-scoped): re-ran
      `_shard_group_key()`'s own `_SHARD_YEAR_RE` regex directly against this doc's own cited VM name
      (`tradfi-bf-cme-ohlcv-1m-g02-6m-cl-2024-20260816-220540`) and confirmed it correctly extracts `"2024"` as the
      shard-year, so the shipped fix structurally covers this launcher family too. Flipped 2026-08-19,
      plan-reconcile observability_master — lead session should still confirm one post-2026-08-17 tradfi
      relaunch-block occurrence (if any) budgets correctly per-shard-year before fully trusting this in production,
      but the decision + implementation are done.
- [ ] [OPERATOR] P3. If A is chosen (or as an interim step regardless), decide whether to manually relaunch just the
      `tradfi-bf-cme-ohlcv-1m-g02-6m-cl-2024` shard now vs waiting for the daily budget reset.

## Progress Log

- 2026-08-16 (slot 11, data_pipeline_failure escalation agt-ee0261): Received escalation for DP-VM-008
  `tradfi-bf-cme-ohlcv-1m-g02-6m-cl-2024-20260816-220540` preempted, `tradfi-bf-cme-ohlcv-1m-` family already at 2/2
  relaunch dispatches today. Checked for an existing issue doc naming this VM/launcher-family/DP-VM-008 class —
  none found (found two same-family DP-VM-001 exit137-stall sibling docs from earlier today, a different alert
  class, and two same-day cefi launcher-family docs covering the identical budget mechanism). Confirmed via
  `gcloud compute instances list` that the exact VM is gone from the live fleet and that the `g02-6m-cl-2024` shard
  is absent from the family's current 36-instance relaunch wave (all other g02-6m-cl years present). Per
  RB-INFRA-RELAUNCH, did not relaunch. Filed this issue doc and paged the operator via `/blocked`. No code changed
  this session.
- 2026-08-17 (slot 1, data_pipeline_failure escalation agt-127f28): Received escalation for DP-VM-008
  `tradfi-bf-cme-ohlcv-1m-g07-xau-zc-2023-20260817-011717` preempted, `tradfi-bf-cme-ohlcv-1m-` family again at 2/2
  relaunch dispatches today (a fresh day's counter — not a continuation of the 2026-08-16 count above). This is the
  family's 4th same-mechanism relaunch-block in 3 calendar days (2026-08-15 ×1 DP-VM-001, -16 ×3 across DP-VM-001
  and this doc, -17 ×1 here). Checked `plans/active/issues/` for an existing open issue doc — this one, still open
  with both operator todos below unresolved — appending here rather than filing a near-duplicate. UNLIKE the
  2026-08-16 `g02-6m-cl-2024` occurrence above: `gcloud compute instances list` confirmed the exact preempted VM
  gone AND found a fresh RUNNING replacement `tradfi-bf-cme-ohlcv-1m-g07-xau-zc-2023-20260817-021631` (~59 min
  later, same zone `asia-northeast1-a`) — confirmed via `read_launch_params()`/`read_progress_checkpoint()` (UTL
  GCS read via `unified_trading_library.get_storage_client()`, never subprocess) that its `LAUNCH_PARAMS.json` is
  byte-identical to the preempted VM's (`VENUE=CME`, `START_DATE=2023-01-01`, `END_DATE=2023-12-31`, same 12-symbol
  XAU/XAV/XAY/YM/ZB/ZC FUT+OPT instrument list, `VM_FORCE=false`) — a genuine same-shard replacement per the
  runbook's "check for an already-running replacement" guidance, not coincidence; no other live instance carries
  the `g07-xau-zc-2023` shard token, so no duplicate-launch risk either (unlike the `cefi-aster-` sibling's
  pollution case). Neither VM has a `PROGRESS.json` checkpoint yet (both too early in their run to have written
  one). **This specific shard needs no operator action** — some mechanism independent of the escalation-dispatch
  path (most likely the family's own periodic/batch relaunch wave, the same shape as the 36-instance single-wave
  launch the 2026-08-16 entry observed) already re-covered it before this escalation was even read. New evidence
  for the still-open P2 decision below: the "un-relaunched shard" cost option A accepts may be smaller in practice
  than assumed, since gaps the escalation-dispatch budget leaves appear to get independently re-covered at least
  some of the time — worth the operator weighing alongside the pending A/B call. Per RB-INFRA-RELAUNCH, did not
  relaunch (moot — a matching replacement was already running). Paged the operator via `/blocked` with this update
  (FYI + recurrence-pattern flag, no new decision blocking). No code changed this session.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries).
- 2026-08-17 (slot 4, data_pipeline_failure escalation agt-18db4c): Received escalation for DP-VM-008
  `tradfi-bf-cme-ohlcv-1m-eth-2022-20260817-090709` preempted, `tradfi-bf-cme-ohlcv-1m-` family again at 2/2
  relaunch dispatches today (same fresh-day counter as the slot-1 entry above — this is the family's 5th
  same-mechanism relaunch-block in 3 calendar days). Checked `plans/active/issues/` for an existing open issue
  doc — this one, still open with both operator todos below unresolved — appending here rather than filing a
  near-duplicate. `gcloud compute instances list --project=central-element-323112
  --filter="name~'^tradfi-bf-cme-ohlcv-1m'"` (whole-project, all zones, 61 RUNNING instances in the current
  ~09:01-09:16Z wave) confirmed the exact preempted VM name is gone AND that `eth-2022` specifically is ABSENT
  from the wave — `eth-2020` and `eth-2021` are both present, `eth-2022` is not, and no other live instance
  anywhere in the fleet carries an `eth-2022` shard token. UNLIKE the slot-1 `g07-xau-zc-2023` entry above (which
  found a same-shard replacement already running), this occurrence matches the ORIGINAL 2026-08-16 `g02-6m-cl-2024`
  shape: confirmed gone, genuinely un-relaunched, no independent mechanism re-covered it this time. Per
  RB-INFRA-RELAUNCH, did not relaunch. Paged the operator via `/blocked` with this update (FYI + recurrence-pattern
  flag naming the now-5th occurrence; no new decision blocking beyond the two open todos below). No code changed
  this session.
- 2026-08-17 (slot 8, data_pipeline_failure escalation agt-e0039e): Received escalation for DP-VM-008
  `tradfi-bf-cme-ohlcv-1m-g04-ho-ng-2026-20260817-110912` preempted, `tradfi-bf-cme-ohlcv-1m-` family again at 2/2
  relaunch dispatches today (same fresh-day counter as the slot-1/slot-4 entries above — this is the family's 6th
  same-mechanism relaunch-block in 3 calendar days). Checked `plans/active/issues/` for an existing open issue
  doc — this one, still open with both operator todos below unresolved — appending here rather than filing a
  near-duplicate. `gcloud compute instances list --project=central-element-323112
  --filter="name~'^tradfi-bf-cme-ohlcv-1m'"` (whole-project, all zones, 46 RUNNING instances in the current
  ~04:07-04:08 PT wave) confirmed the exact preempted VM name is gone (exact-name filter returns zero rows) AND
  that `g04-ho-ng-2026` specifically is ABSENT from the wave — `g04-ho-ng-2020/2021/2023/2024` are all present,
  `2026` is not, and no other live instance anywhere in the fleet carries a `g04-ho-ng-2026` shard token. Matches
  the ORIGINAL 2026-08-16 `g02-6m-cl-2024` and slot-4 `eth-2022` shape: confirmed gone, genuinely un-relaunched, no
  independent mechanism re-covered it this time. Per RB-INFRA-RELAUNCH, did not relaunch. Paged the operator via
  `/blocked` with this update (FYI + recurrence-pattern flag naming the now-6th occurrence; no new decision
  blocking beyond the two open todos below). No code changed this session.
- 2026-08-17 (slot 16, data_pipeline_failure escalation agt-938528): Received escalation for DP-VM-008
  `tradfi-bf-cme-ohlcv-1m-g01-6a-6l-2025-20260817-130324` preempted, `tradfi-bf-cme-ohlcv-1m-` family again at 2/2
  relaunch dispatches today (same fresh-day counter as the slot-1/4/8 entries above — this is the family's 7th
  same-mechanism relaunch-block in 3 calendar days). Checked `plans/active/issues/` for an existing open issue
  doc — this one, still open with both operator todos below unresolved — appending here rather than filing a
  near-duplicate. `gcloud compute instances list --project=central-element-323112
  --filter="name~'^tradfi-bf-cme-ohlcv-1m'"` (whole-project, all zones, 18 RUNNING/STOPPING instances in the
  current ~13:10-13:16 UTC wave, groups g05/g06/g07 only) confirmed the exact preempted VM name is gone
  (exact-name filter returns zero rows) AND that no `g01-*` instance of any shard/year exists anywhere in the
  fleet right now (`^tradfi-bf-cme-ohlcv-1m-g01` filter also returns zero rows) — the current wave doesn't even
  cover the g01 group at all. Matches the ORIGINAL 2026-08-16 `g02-6m-cl-2024`, slot-4 `eth-2022`, and slot-8
  `g04-ho-ng-2026` shape: confirmed gone, genuinely un-relaunched, no independent mechanism re-covered it this
  time. Per RB-INFRA-RELAUNCH, did not relaunch. Paged the operator via `/blocked` with this update (FYI +
  recurrence-pattern flag naming the now-7th occurrence; no new decision blocking beyond the two open todos
  below). No code changed this session.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- **2026-08-21 (operator ruling D5, Databento CME billing — operator paying)**: the daily `tradfi-bf-cme-ohlcv-1m-`
  relaunch volume this doc chronicles (and the "moots the relaunch-bound tightening" framing in D5's own question)
  traces to a separate, undocumented crontab entry on the AO orchestrator VM's `ubuntu` user running
  `scripts/wave_launcher.py` every 3h at `WAVE_MAX_CONCURRENT=20` — NOT the Terraform-managed
  `uts-prod-tradfi-wave-launcher-cron` Cloud Scheduler job (confirmed still `state: PAUSED` since 2026-06-24). Paused
  at the source (crontab entry commented out on the orchestrator VM) and a live GLBX.MDP3 billing-probe gate shipped
  into `wave_launcher.py` as defense-in-depth. Full writeup + evidence:
  `/plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md` Progress Log. This doc's remaining
  open P3 todo (manually relaunch `g02-6m-cl-2024` now vs. wait) is now moot either way while CME billing stays
  blocked — a manual relaunch would hit the same 402 wall; left open as-is, not force-closed, since the underlying
  A-vs-B relaunch-budget-shape decision it references is a separate, already-`[x]`-resolved question (option B,
  shipped `deployment-service@2058bab339`).
