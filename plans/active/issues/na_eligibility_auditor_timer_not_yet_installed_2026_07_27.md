---
doc_type: issue
title: na-eligibility-auditor daily timer is shipped but not yet installed on the central orchestrator VM
summary:
  All code for the new /na-eligibility-audit daily dispatch (plan_health.py mode, agents/na_eligibility_auditor.md,
  install-na-eligibility-auditor-timer.sh) is committed and pushed to live-defi-rollout, but the systemd timer/service
  units themselves have not been installed on the real central orchestrator VM — that install step needs to run there,
  not from a dev checkout.
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [na-eligibility-audit, timer-rollout, ao-dispatch, follow-up]
related:
  [
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/active/ag_closeout_audit_rollout_2026_07_25.md,
  ]
created: "2026-07-27"
parent_epic: orchestrator_master
priority: P2
source: >-
  Session 2026-07-27, building /na-eligibility-audit as a sibling to /ag-closeout-audit/plan-reconcile/docs-reconcile.
  The three sibling timers (plan-reconciler, docs-reconciler, ag-closeout-auditor) were already live on the central VM
  when this session started; this fourth one only reaches parity once actually installed there too.
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# na-eligibility-auditor timer not yet installed

**What's shipped** (verify with `git log`, not this doc, before acting — these are point-in-time citations):

- `unified-trading-pm@f355c0b2a` — `/na-eligibility-audit` skill,
  `codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`, `check_na_corpus_ratchet.py` + baseline,
  `agents/na_eligibility_auditor.md`, cross-references in the sibling skills.
- `agent-orchestrator@f4a116e` — `mode="na_eligibility"` in `server/plan_health.py`, `server/models/escalation.py` doc
  update, `scripts/install-na-eligibility-auditor-timer.sh`.

**What's NOT done**: the install script has never been run. On the central VM:

```bash
cd agent-orchestrator && sudo bash scripts/install-na-eligibility-auditor-timer.sh
```

This installs `na-eligibility-auditor.timer`/`.service` (default fire time 07:00 UTC, staggered 2h after
`ag-closeout-auditor.timer`'s 05:00 UTC). Until this runs, the daily NA-eligibility audit never fires on its own — it's
only reachable via a manual `POST /api/plan-health/dispatch {"mode": "na_eligibility"}` or an interactive
`/na-eligibility-audit` invocation.

- [ ] [OPERATOR] P2. Run `sudo bash scripts/install-na-eligibility-auditor-timer.sh` on the central orchestrator VM,
      then verify with `systemctl status na-eligibility-auditor.timer` and a manual
      `sudo systemctl start na-eligibility-auditor.service` test-fire (mirrors how the other 3 sibling timers were
      verified live). **Done when**: `systemctl list-timers` shows `na-eligibility-auditor.timer` next-fire ≤24h out,
      and one real dispatch (`agent_kind=na_eligibility_auditor` in the agents table) has completed
      `lifecycle-complete`.

This is an infra/VM-access action (installing a systemd unit on the shared central VM) rather than a repo-code change,
which is why it's tracked here instead of folded into the code commits above.
