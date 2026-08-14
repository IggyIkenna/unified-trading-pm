---
doc_type: issue
title:
  "Fleet git-health scanner repeatedly re-flags ip-172-31-0-185 (slots 0-2) as a stale/dead host — it is the operator's
  LIVE human-planning VM (i-0dd9812a96cdda5dc); its dirty repos are operator interactive WIP, NOT orphaned worker WIP"
summary: >-
  Successive review incarnations keep re-discovering host ip-172-31-0-185 (private IP) as reporter_stale / ff_cron_stale
  with 5 dirty repos never recovered (market-tick-data-service, strategy-service, system-integration-tests,
  unified-api-contracts, unified-trading-pm), and reasonably ask whether it's a decommissioned host with orphaned WIP.
  It is NOT. AWS-verified (twice, 2026-08-03): private-ip 172.31.0.185 = instance i-0dd9812a96cdda5dc, state=RUNNING,
  Name=agent-orch-human-planning-vm, launched 2026-07-14. It's the operator's interactive-only dev box, so it doesn't
  run the fleet ff-cron and its local checkouts get mislabeled "slots 0-2" by the worker scanner (same slot-id namespace
  as the real orchestrator host ip-172-31-5-118). The 5 dirty repos are the OPERATOR's own interactive working state —
  do NOT rescue/inherit them (that would clobber the operator's in-progress work). Filed durably so the next fleet
  git-health incarnation inherits this instead of re-flagging it every recycle.
status: resolved
nature: notes
asset_group:
  [ao] # corrected 2026-08-04 (ag-closeout-audit ao tranche run) -- was [cross-cutting]. AO fleet git-health
  # scanner false-positive, not cross-AG content.
stage: [meta]
repos: [unified-trading-pm]
scope: [admin]
tags: [fleet-git-health, human-planning-vm, false-positive, scanner-allowlist, per-tab-worktrees]
related: [/codex/05-infrastructure/per-tab-worktrees.md, /codex/04-architecture/runtime-deployment-topology.md]
created: 2026-08-03
author: unknown
parent_epic: agent_operating_framework_master
priority: P3
assigned_vm: NA
execution_scope: local-only
resolved_by: "interactive session, 2026-08-05 — confirmed VM terminated 2026-08-03 (not replaced), allowlist todo moot"
locked_by:
source:
  "recurring review fleet-git-health re-flags (msgs #3552, #3581, #3585, 2026-08-03), each independently re-discovering
  the same known-benign host; AWS-verified by main agt-1756f6"
drift_direction: advance-process
estimate_class: infra
depends_on: []
context_scope:
  [
    agent-orchestrator/server/routes/git_health.py,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/04-architecture/runtime-deployment-topology.md,
  ]
---

# ip-172-31-0-185 is the LIVE human-planning VM — a known scanner false-positive, do NOT rescue its WIP

## The recurring finding

The fleet git-health scanner reports host `ip-172-31-0-185` (surfaced as slots 0-2) with `reporter_stale=True`,
`ff_cron_stale=True`, and 5 dirty repos untouched since 2026-07-25/28. Successive review incarnations keep
re-discovering it and asking whether it's a decommissioned host whose worker WIP was never rescued.

## Why it's a false-positive (AWS-verified twice, 2026-08-03)

`aws ec2 describe-instances --filters Name=private-ip-address,Values=172.31.0.185` → `i-0dd9812a96cdda5dc`,
**state=RUNNING**, **Name=`agent-orch-human-planning-vm`**, launched 2026-07-14.

- It is the **operator's live, interactive-only human-planning VM** — NOT a worker host, NOT decommissioned.
- It doesn't run the fleet ff-cron, so `reporter_stale`/`ff_cron_stale` are EXPECTED, not a health problem.
- Its local checkouts get mislabeled "slots 0-2" by the worker scanner because they share the slot-id namespace with the
  real orchestrator host `ip-172-31-5-118` (two different machines, overlapping ids in the scanner).
- **The 5 dirty repos are the OPERATOR's own interactive working state** — this is categorically different from a dead
  worker slot's orphaned WIP. Do NOT run inherited-dirty-WIP / orphan-rescue on it; a rescue would clobber the
  operator's in-progress work. (Contrast: the per-tab-worktrees LIVENESS-gated inherit rule applies to DEAD worker
  slots, not to a live operator interactive box.)

## Todos

- [x] [INFRA] P3. **MOOT 2026-08-05 — the VM this todo was allowlisting no longer exists.** Definitively resolved the
      "is it terminated or replaced" ambiguity raised in the 2026-08-04 discrepancy entry below: `i-0dd9812a96cdda5dc`
      was deliberately terminated 2026-08-03 (operator-approved retirement,
      `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`), NOT replaced — re-confirmed 2026-08-05
      (`aws ec2 describe-instances` returns empty for the instance ID). No allowlist entry is needed for a host that no
      longer exists; the scanner will naturally stop reporting it once its stale-host cache ages out. **Separately, real
      bad news**: `per_slot_ff_pull_status_report_crons_stale_fleet_wide_2026_07_27.md`'s P1 WIP-preservation warning
      for this same host was never actioned before termination — see that doc for the (likely unrecoverable) outcome.

## Progress Log

- **2026-08-03 (main agt-1756f6)**: Filed after the 3rd+ independent review re-flag (#3585) of this known-benign host.
  Re-verified via AWS both times; the answer is stable. This doc is the durable record so future incarnations
  self-resolve. The only open action is the scanner allowlist (INFRA todo above) — until that lands, expect the re-flag
  to recur; point re-flaggers here.
- **context-scout 2026-08-03**: populated context_scope (3 entries) — the doc's own todo hedges between
  deployment-service and agent-orchestrator as "the scanner's home"; grep-confirmed the actual scanner source
  (reporter_stale/ff_cron_stale logic) lives in agent-orchestrator, not deployment-service — a red herring worth
  flagging to whoever picks up the todo.
- **na-eligibility-audit 2026-08-04** (autonomous, tranche `ao`): KEEP-NA, valid — first marker on this doc. The sole
  open todo (allowlist the human-planning VM in the fleet git-health scanner) is bounded/mechanical on its own, but its
  content is already extracted verbatim into `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch6_2026_08_04.md` todo
  9 (same-day sibling `/ag-closeout-audit ao` run) — that batch, per this tranche's own 100%-consistent,
  previously-flagged convention (`ao_open_issues_consolidated_close_out_2026_07_17.md:136`, na-eligibility-audit
  2026-08-01), stays `assigned_vm: NA`/interactive-only even once its extracted content clears AO-dispatch-scope
  eligibility. Reclassifying this source doc directly would create a competing/duplicate dispatch claim against batch6
  once it activates — not flipped, per the shared conflict-check protocol
  (`ao-dispatch-batch-naming-and-conflict-check.md` § 3, surface (b)).
- **2026-08-04 (main agt-1756f6) — NEW DISCREPANCY to confirm (review re-flag #3685)**: another review incarnation
  re-flagged this host (now reading it as "dead/decommissioned, a retired/replaced prior instance") and asked whether to
  recover slot-0's WIP or stop polling it. On re-verifying I hit a discrepancy with the 08-03 "RUNNING" finding: from my
  `ikenna-worker` AWS identity (account 427895769566, ap-northeast-1)
  `aws ec2 describe-instances --instance-ids i-0dd9812a96cdda5dc` returns EMPTY, and an unfiltered `describe-instances`
  shows only `i-0c9b283b31d6b5ca7` (agent-orchestrator-vm-1 / 172.31.5.118, this host) and `i-042a6332509482556`
  (ci-escalation-runner-vm-1 / 172.31.3.59) — NOT `i-0dd9812a96cdda5dc`. So my identity CAN see EC2 but NOT the
  human-planning VM. This is **ambiguous**, two readings and I cannot disambiguate from the worker identity: (a) the VM
  was terminated/replaced since the 08-03 verification (review's hypothesis), or (b) `ikenna-worker` has an
  instance-visibility boundary and the 08-03 verification used broader (operator) creds. **Action: did NOT overturn
  protect-not-inherit and did NOT rescue slot-0's WIP** — if it's still the operator's live box, rescuing clobbers live
  work; if it was replaced, write-off needs operator confirmation first, not a worker-identity guess. Flagged to the
  operator (via review reply to #3685) to confirm the human-planning VM's current state from operator creds; if
  confirmed decommissioned, the slot-0 dirty repos (mtds/strategy-service/SIT/UAC/pm, frozen 07-22..24) get a real
  recovery pass and the `[INFRA]` allowlist todo above should target the REPLACEMENT instance-id.
- **2026-08-05 (interactive session)**: definitively resolved the (a)/(b) ambiguity above — **(a) confirmed**, the VM
  was deliberately terminated 2026-08-03 by a separate session executing
  `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`'s operator-approved retirement todo, not replaced. There is
  no replacement instance-id to redirect the (now-moot) allowlist todo to. The real fallout is documented in
  `per_slot_ff_pull_status_report_crons_stale_fleet_wide_2026_07_27.md`: the slot-0 WIP-recovery pass this doc's 08-04
  entry called for never happened before termination, and no snapshot/volume survives to attempt it now.
