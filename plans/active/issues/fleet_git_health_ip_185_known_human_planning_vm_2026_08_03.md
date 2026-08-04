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
status: open
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
parent_epic: agent_operating_framework_master
priority: P3
assigned_vm: NA
execution_scope: local-only
resolved_by:
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

- [ ] [INFRA] P3. Add `i-0dd9812a96cdda5dc` (ip-172-31-0-185) to the fleet git-health scanner's known-hosts allowlist /
      annotate it as the human-planning VM, so it stops surfacing as a stale worker host and reviewers stop re-flagging
      it. (repo: the scanner's home — deployment-service or agent-orchestrator; worker/operator change, not main's —
      main cannot push code.)

## Progress Log

- **2026-08-03 (main agt-1756f6)**: Filed after the 3rd+ independent review re-flag (#3585) of this known-benign host.
  Re-verified via AWS both times; the answer is stable. This doc is the durable record so future incarnations
  self-resolve. The only open action is the scanner allowlist (INFRA todo above) — until that lands, expect the re-flag
  to recur; point re-flaggers here.
- **context-scout 2026-08-03**: populated context_scope (3 entries) — the doc's own todo hedges between
  deployment-service and agent-orchestrator as "the scanner's home"; grep-confirmed the actual scanner source
  (reporter_stale/ff_cron_stale logic) lives in agent-orchestrator, not deployment-service — a red herring worth
  flagging to whoever picks up the todo.
