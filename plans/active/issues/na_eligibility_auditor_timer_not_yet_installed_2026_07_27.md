---
doc_type: issue
title: na-eligibility-auditor installed + procedure proven interactively, first unsupervised cron fire not yet verified
summary:
  All code for the new /na-eligibility-audit daily dispatch is shipped, the systemd timer is installed + enabled on the
  central orchestrator VM (verified active/waiting, next fire 2026-07-28 07:01 UTC), unit tests cover the plan_health.py
  dispatch wiring (agent-orchestrator@a935dcd85), and the skill's own Phase 0-5 procedure has now been run interactively
  end-to-end against the live tradfi tranche (unified-trading-pm@b5172a64c + c00860d74) with real, useful results — see
  the dry-run Progress Log entry below. The one remaining open question is whether the DAILY CRON path (opus/effort-max
  dispatch mode, tranche-sharded, lifecycle-complete registration) fires and completes correctly on its own,
  unsupervised.
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
assigned_vm: planning
assigned_role: infra
sequential: true # both todos touch the same timer/install-script + the same first-fire verification surface
resolved_by:
locked_by:
context_scope:
  [
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/archive/issues/ao_scheduled_job_observability_and_slack_alerting_2026_07_28.md,
    agent-orchestrator/server/plan_health.py,
  ]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# na-eligibility-auditor: installed + unit-tested + procedure proven interactively

**What's shipped** (verify with `git log`, not this doc, before acting — these are point-in-time citations):

- `unified-trading-pm@f355c0b2a` — `/na-eligibility-audit` skill,
  `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`, `check_na_corpus_ratchet.py` +
  baseline, `agents/na_eligibility_auditor.md`, cross-references in the sibling skills.
- `agent-orchestrator@f4a116e` — `mode="na_eligibility"` in `server/plan_health.py`, `server/models/escalation.py` doc
  update, `scripts/install-na-eligibility-auditor-timer.sh`.
- `agent-orchestrator@a935dcd85` — unit tests for the `na_eligibility` dispatch mode (smart-tier forcing, tranche
  threading, report-gate exemption, `agent_kind` registration), mirroring the existing per-mode pattern. This closed a
  real gap: the mode shipped without dedicated tests, only riding along on a full-suite pass that didn't exercise it.

**What's still open — not a code gap, a verification gap**: the skill's Phase 0-5 procedure has now been run
interactively (see below) and works as designed. What's NOT yet verified is the DAILY CRON path specifically —
opus/effort-max forcing, tranche-sharded concurrent dispatch, `agent_kind=na_eligibility_auditor` reaching
`lifecycle-complete` in the agents table. That's operational/dispatch-wiring verification, not skill-logic verification,
and it's still only provable by the timer's own first real fire.

- [x] [INFRA] P2. **RETAGGED 2026-07-28 (workspace stale-gate audit) — already executed and verified, operator action
      complete.** Run `sudo bash scripts/install-na-eligibility-auditor-timer.sh` on the central orchestrator VM — DONE
      2026-07-27 via `aws ssm send-command` (instance `i-0c9b283b31d6b5ca7`, region `ap-northeast-1`, operator
      unlock-authorized this session). `git pull --ff-only` first picked up `agent-orchestrator@f4a116e` clean.
      Verified: `systemctl status na-eligibility-auditor.timer` → `Loaded: loaded ... enabled`,
      `Active: active     (waiting)`, `Trigger: Tue 2026-07-28 07:01:01 UTC; 16h left` (well within the ≤24h bar).
- [x] [REVIEW] P2. **Interactive dry-run of the skill's own Phase 0-5 procedure — DONE 2026-07-27.** Ran
      `/na-eligibility-audit` on the `tradfi` tranche (32 docs, smallest tranche with zero collision risk against a
      concurrent agent's live asset_group-reclassification sweep at the time — `ci`/`ao`/`infra` were 65-97% dirty from
      that unrelated sweep, `tradfi` was 0%). 3 sonnet-tier read-only sub-agents classified 21 in-scope docs (all
      `open_todos ≥ 1`, none pre-verdicted): 8 KEEP-NA valid, 5 KEEP-NA stale-items, 3 KEEP-NA-STALE already-duplicated,
      5 RECLASSIFY. Phase 2 conflict-check against every active
      `parent_epic:     {tradfi,infrastructure,instruments}_master` planning doc caught 2 real findings a naive apply
      would have missed: (a) `tradfi_backfill_throughput_followups_2026_07_24.md`'s 2 flagged items were already
      claimed, combined into one todo, in the ALREADY-active `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md` — held
      back, annotated, not reclassified (would have duplicated live dispatched work); (b) a full direct re-read of
      `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` (done before authoring its extraction
      batch, since the doc has 14 open items and the classifying sub-agent's first pass had only surfaced 6) found the
      "CLOB-on-chain HYPERLIQUID/ASTER" item already shipped elsewhere
      (`market-tick-data-service@1fff193b88d3331471ed01519e02e79071e74b81`, confirmed via
      `infra_capture_and_devops_leftovers_2026_07_06.md`'s own checkbox) — closed with citation instead of extracted.
      Shipped: 2 new AO-dispatch docs (`infra_satellite_ao_dispatch_batch2_2026_07_27.md`, 9 todos, 3 sources;
      `instruments_satellite_ao_dispatch_batch1_2026_07_27.md`, 5 todos, 1 source) + their gated finalize twins, plus
      stale-checkbox/citation fixes across 9 existing docs — `unified-trading-pm@b5172a64c`. NA-corpus ratchet
      re-measured 360 docs/1421 open todos (was 362/1431) and the baseline was lowered to lock in the shrink —
      `unified-trading-pm@c00860d74`. **Process finding worth carrying forward**: a sonnet-tier classification sub-agent
      can under-read a long, information-dense doc even when explicitly told to read end-to-end — the 1-of-21 miss here
      was caught only because Phase 2's own conflict-check work required tracing the doc's references closely enough to
      notice the count didn't add up. A future run (interactive or cron) should treat a sub-agent's reported open-item
      count as checkable against `grep -cE '^- \[ \]'` on the source doc, not trusted blind.
- [ ] [SCRIPT] P3. Confirm the timer's FIRST real scheduled fire (2026-07-28 ~07:01 UTC) actually completes —
      `agent_kind=na_eligibility_auditor` reaching `lifecycle-complete` in the agents table, same verification the other
      3 sibling timers got on their own first live run. Not forced manually this session (a manual `systemctl start`
      would spawn a real opus/effort-max worker doing real corpus writes — out of scope for a pure install-verification
      step); the natural next-day fire is the intended first real test. Distinct from the item above: this verifies the
      DISPATCH WIRING (timer → opus worker → lifecycle-complete), not the skill's own logic (already proven above).
- [ ] [SCRIPT] P2. **Re-tune `na_eligibility_auditor`'s per-tranche timeout budget** — the timer's FIRST real fire
      (2026-07-28 07:00 UTC, confirming the item above's answer is "no, not yet") hit `Active: failed`: a curl
      `TIMEOUT`/`HTTP:000` past its own `--max-time 2400`/`TimeoutStartSec=2450` on multiple tranches. That budget was
      carried over unmeasured from the 2026-07-26 sharding change (the dispatch script's own comment already flagged "no
      measurement of a single-tranche run exists yet"). Now that `ScheduledJobRunRow` durably records per-tranche
      start/finish timing (`agent-orchestrator`, shipped 2026-07-28 — see
      `/plans/archive/issues/ao_scheduled_job_observability_and_slack_alerting_2026_07_28.md`), bump the timeout (or
      diagnose why a single tranche exceeds 40 min) once a few more real data points land in that table.

This is an infra/VM-access action (installing a systemd unit on the shared central VM) rather than a repo-code change,
which is why it's tracked here instead of folded into the code commits above.

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY → planning, conflict-cleared — both open todos are bounded operational
  verifications with stated gates and an existing tool: confirm `agent_kind=na_eligibility_auditor` reaches
  `lifecycle-complete` (read-only SSM, the same path the 3 sibling timers were verified on), and re-tune the per-tranche
  timeout after the 2026-07-28 first fire hit `Active: failed` on a curl `TIMEOUT` past its own unmeasured
  `--max-time 2400`. The blocking dependency has landed: `ScheduledJobRunRow` has recorded durable per-tranche
  start/finish timing since 2026-07-28, so the 'wait for a few more data points' gate is satisfiable now. No operator
  authority, no design fork. **Phase-2 conflict-check**: the only `na_eligibility` hits on the active planning surface
  are incidental prose references to the agent_kind in
  `cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29.md` and `blrs_g3_g10_rescope_2026_07_28.md` —
  neither claims the timer budget or the install script. CLEAR. Set `assigned_role: infra`, `sequential: true` (both
  todos touch the same timer/install-script + first-fire verification surface).
- **na-eligibility-audit 2026-08-01** (autonomous, tranche `ao`, dispatch agt-8e95ca, slot 2): **apply-gap fix, not a
  fresh reclassification decision.** Re-verified: `assigned_vm` in this doc's frontmatter still read `NA` despite the
  2026-07-30 entry above recording a conflict-cleared RECLASSIFY verdict with `assigned_role`/`sequential` already set —
  the flip itself was reasoned through but never actually applied to the doc. Fixed now: `assigned_vm: NA -> planning`,
  `execution_scope: local-only -> orchestrator-agent`. No new conflict-check needed (the 2026-07-30 one already covered
  this exact surface and nothing material has changed since). Flagging as a process note for whoever next touches this
  skill's own Phase 3: a "RECLASSIFY, conflict-cleared" Progress Log entry is not sufficient proof of an applied flip —
  always diff the entry's stated verdict against the doc's ACTUAL current frontmatter before trusting it.
