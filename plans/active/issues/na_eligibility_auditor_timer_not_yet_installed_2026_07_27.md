---
doc_type: issue
title: na-eligibility-auditor daily timer installed, first real scheduled fire not yet verified
summary:
  All code for the new /na-eligibility-audit daily dispatch is shipped, and the systemd timer is installed + enabled on
  the central orchestrator VM (verified active/waiting, next fire 2026-07-28 07:01 UTC). Unit tests now cover the
  plan_health.py dispatch wiring (agent-orchestrator@a935dcd85), but the skill's own Phase 0-5 procedure has never
  actually run against the live corpus — neither via the cron's first fire nor an interactive dry-run. That's the one
  open question left for whoever picks this up.
status: open
nature: process
asset_group: [ao]
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

# na-eligibility-auditor: installed + unit-tested, procedure itself never run

**What's shipped** (verify with `git log`, not this doc, before acting — these are point-in-time citations):

- `unified-trading-pm@f355c0b2a` — `/na-eligibility-audit` skill,
  `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`, `check_na_corpus_ratchet.py` +
  baseline, `agents/na_eligibility_auditor.md`, cross-references in the sibling skills.
- `agent-orchestrator@f4a116e` — `mode="na_eligibility"` in `server/plan_health.py`, `server/models/escalation.py` doc
  update, `scripts/install-na-eligibility-auditor-timer.sh`.
- `agent-orchestrator@a935dcd85` — unit tests for the `na_eligibility` dispatch mode (smart-tier forcing, tranche
  threading, report-gate exemption, `agent_kind` registration), mirroring the existing per-mode pattern. This closed a
  real gap: the mode shipped without dedicated tests, only riding along on a full-suite pass that didn't exercise it.

**What's still open — not a code gap, a verification gap**: no agent has ever actually run the skill's own Phase 0-5
procedure against the live corpus. The timer's first natural fire is 2026-07-28 ~07:01 UTC (unsupervised, autonomous
mode). An interactive dry-run on one small tranche first (so the output can be reviewed before the cron's first
unsupervised swing) was offered in the building session but not yet actioned.

- [x] [OPERATOR] P2. Run `sudo bash scripts/install-na-eligibility-auditor-timer.sh` on the central orchestrator VM —
      DONE 2026-07-27 via `aws ssm send-command` (instance `i-0c9b283b31d6b5ca7`, region `ap-northeast-1`, operator
      unlock-authorized this session). `git pull --ff-only` first picked up `agent-orchestrator@f4a116e` clean.
      Verified: `systemctl status na-eligibility-auditor.timer` → `Loaded: loaded ... enabled`,
      `Active: active     (waiting)`, `Trigger: Tue 2026-07-28 07:01:01 UTC; 16h left` (well within the ≤24h bar).
- [ ] [SCRIPT] P3. Confirm the timer's FIRST real scheduled fire (2026-07-28 ~07:01 UTC) actually completes —
      `agent_kind=na_eligibility_auditor` reaching `lifecycle-complete` in the agents table, same verification the other
      3 sibling timers got on their own first live run. Not forced manually this session (a manual `systemctl start`
      would spawn a real opus/effort-max worker doing real corpus writes — out of scope for a pure install-verification
      step); the natural next-day fire is the intended first real test.
- [ ] [REVIEW] P2. **Alternative to the above, if picked up before 2026-07-28 07:01 UTC**: run `/na-eligibility-audit`
      interactively on ONE small tranche (e.g. `mtds_mdps`/`observability` — smallest NA population per
      `generate_na_doc_tranche_inventory.py`) with the operator present to review verdicts before anything is applied,
      rather than letting the cron's first-ever run be fully unsupervised. Offered mid-session, not yet
      answered/actioned — do this OR the P3 above, not necessarily both.

This is an infra/VM-access action (installing a systemd unit on the shared central VM) rather than a repo-code change,
which is why it's tracked here instead of folded into the code commits above.
