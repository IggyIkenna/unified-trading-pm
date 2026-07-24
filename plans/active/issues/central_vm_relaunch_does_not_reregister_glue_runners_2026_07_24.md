---
doc_type: issue
title:
  "launch-central-brain-aws.sh's from-scratch relaunch of the planning VM does not re-provision the self-hosted GitHub
  Actions glue/glue-writer runner pool also hosted on that box — a relaunch after the current VM dies would leave ~39 CI
  workflows hung waiting for runners that will never come back"
summary:
  The planning VM (i-0c9b283b31d6b5ca7, EIP 13.113.200.22) hosts two independent things today — the agent-orchestrator
  backend + slot fleet, and a self-hosted GitHub Actions runner pool ("glue"/"glue-writer") that ~39 unified-trading-pm
  CI workflows route through via a `[self-hosted, glue]` runner label. `launch-central-brain-aws.sh` already covers
  disaster recovery for the first (from-scratch relaunch + EIP reassociation, near-instant, DNS stays valid) but says
  nothing about the second. A relaunch today would bring AO back but leave every glue-routed workflow queued forever
  until someone remembers to manually run `setup-glue-runners.sh install` on the new box.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, disaster-recovery, self-hosted-runners, ci-cd, planning-vm]
related:
  [/plans/active/issues/ao_docs_reconciliation_2026_07_15.md, /codex/05-infrastructure/local-tmux-precompact-watcher.md]
created: 2026-07-24
last_updated: 2026-07-24
priority: P2
parent_epic: infrastructure_master
source:
  "Surfaced while ruling on the epic-VM code-artifact deletion (operator 2026-07-24) — operator asked for the planning
  VM's failover story specifically to include re-registering GH-workflow runners, not just relaunching AO"
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

## What's there today

- **`deployment-service/scripts/vm/launch-central-brain-aws.sh`** — canonical from-scratch relaunch of the central box.
  Re-associates the Elastic IP (`13.113.200.22`, near-instant, DNS stays valid), then runs
  `agent-orchestrator/scripts/bootstrap_vm.sh --role planning` to bring the AO backend + 5 interactive slots back up.
  Confirmed independent of the epic-VM launchers removed today (`deployment-service@7438ec5`) — this script's own header
  comment says so explicitly ("The epic launcher … must NOT be used for this box").
- **`unified-trading-pm/scripts/self-hosted-runners/`** — a SEPARATE, manually-installed self-hosted GitHub Actions
  runner pool (`glue`, JIT-ephemeral; `glue-writer`, long-lived) that also runs on this same VM (`ubuntu` user, ambient
  creds, per `README.md` "Isolation scope"). `classify-glue-workflows.sh` currently routes **39** unified-trading-pm
  workflows through `runs-on: [self-hosted, glue]` (a 40th, `ci-status-update`, through `glue-writer`).

## The gap

Nothing wires the two together. `bootstrap_vm.sh --role planning` provisions AO; it has no knowledge of, and does not
call, `setup-glue-runners.sh install`. So the sequence "current VM dies → operator runs `launch-central-brain-aws.sh`"
brings AO back online but the glue/glue-writer runner registrations are GONE (they lived only on the dead box) — every
workflow with `runs-on: [self-hosted, glue*]` queues forever with no runner to claim it, silently, until someone notices
CI is stuck and remembers this pool exists and needs manual reinstall.

Checked: no runbook or codex doc currently ties central-VM relaunch to glue-runner reinstall
(`grep -rl "launch-central-brain\|central-brain" codex/15-runbooks/ codex/05-infrastructure/` → 0 hits pairing the two).

## Proposed fix (not yet built — operator to choose the shape)

Two options, not mutually exclusive:

1. **Wire it into the relaunch script.** Add a step to `launch-central-brain-aws.sh`'s bootstrap (or a follow-on step
   documented in its own header) that runs `setup-glue-runners.sh install` once the AO backend is up — makes the
   relaunch actually complete DR, not partial DR.
2. **Document it as an explicit post-relaunch step** in a new or existing runbook (`codex/15-runbooks/`, alongside the
   existing `agent-orchestrator-failover-re-enable-checklist.md`) with `owner`/`cadence`/`verifier` — cheaper, but
   relies on a human remembering it during an incident, which is exactly the failure mode DR runbooks exist to avoid.

## Open todos

- [ ] [OPERATOR] P2. Decide which of the two shapes above (or both), and whether this is worth doing now or deferring —
      it has never actually been exercised (no VM has died and been relaunched in production), so this is hardening
      ahead of an incident, not a fix for one that happened.
- [ ] [SCRIPT] P2. Once ruled: implement the chosen fix (script wiring and/or runbook), and prove it — the gate should
      be a real or simulated relaunch where a glue-routed workflow (e.g. `reconcile-release-tags`, the documented
      canary) picks up a runner on the NEW box without manual intervention beyond what the runbook states.

## Progress Log

- **2026-07-24**: Filed while ruling on the epic-VM code-artifact deletion — the operator's actual ask ("we just need
  failover protection... also register that vm for the github workflows") surfaced this gap, which is real and
  previously undocumented. Not resolved here; awaiting operator decision on shape.
